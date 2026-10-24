"""Popülerlik modeli için veri hazırlama ve özellik üretimi."""

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold

HIT_ESIGI = 60  # popülerliği bu değer ve üstü olan şarkılar "hit" sayılır (~en üst %12)


def surumleri_birlestir(df: pd.DataFrame) -> pd.DataFrame:
    """Aynı sanatçının aynı adlı şarkısının farklı sürümlerinden (single, albüm,
    derleme) yalnızca en popüler olanını bırakır.

    Spotify her sürümü ayrı puanlar ve dinlenmeler genelde tek sürümde toplanır;
    diğer sürümler 0'a yakın popülerlik alır. Birleştirmezsek model aynı sesi
    hem "hit" hem "0" olarak görür ve neredeyse aynı satırlar eğitim ile test
    arasında bölünür.
    """
    anahtar = (df["artists"].str.lower().str.strip() + "|"
               + df["track_name"].str.lower().str.strip())
    return (df.assign(_anahtar=anahtar)
              .sort_values("popularity", ascending=False, kind="stable")
              .drop_duplicates("_anahtar")
              .drop(columns="_anahtar")
              .reset_index(drop=True))


def ana_sanatci(df: pd.DataFrame) -> pd.Series:
    """Birden fazla sanatçı ';' ile ayrılmış; ilk sanatçıyı döndürür."""
    return df["artists"].str.split(";").str[0].str.strip()


def _yumusatilmis_ortalama(egitim: pd.DataFrame, uygula: pd.DataFrame,
                           genel_ort: float, m: float) -> np.ndarray:
    istatistik = egitim.groupby("ana_sanatci")["popularity"].agg(["sum", "count"])
    deger = (istatistik["sum"] + m * genel_ort) / (istatistik["count"] + m)
    return uygula["ana_sanatci"].map(deger).fillna(genel_ort).to_numpy()


def sanatci_kodla(egitim: pd.DataFrame, test: pd.DataFrame, m: float = 5,
                  kat_sayisi: int = 5, random_state: int = 42) -> tuple[np.ndarray, np.ndarray]:
    """Sanatçının *diğer* şarkılarının ortalama popülerliğini özellik olarak üretir.

    Sızıntıyı önlemek için:
    - Test satırları yalnızca eğitim verisinden hesaplanan ortalamalarla kodlanır.
    - Eğitim satırları K-katlı (out-of-fold) kodlanır; bir şarkının kendi
      popülerliği kendi özelliğine karışmaz.
    - Az şarkısı olan sanatçılar genel ortalamaya doğru çekilir (m = yumuşatma gücü);
      hiç görülmemiş sanatçılar genel ortalamayı alır.

    Her iki DataFrame'de de `ana_sanatci` ve `popularity` sütunları olmalı.
    """
    egitim_kod = np.zeros(len(egitim))
    katlar = KFold(kat_sayisi, shuffle=True, random_state=random_state)
    for fit_idx, uygula_idx in katlar.split(egitim):
        fit = egitim.iloc[fit_idx]
        # Genel ortalama da yalnızca diğer katlardan; yoksa satırın kendi değeri
        # yumuşatma terimi üzerinden kendi özelliğine sızar.
        egitim_kod[uygula_idx] = _yumusatilmis_ortalama(
            fit, egitim.iloc[uygula_idx], fit["popularity"].mean(), m)
    test_kod = _yumusatilmis_ortalama(egitim, test, egitim["popularity"].mean(), m)
    return egitim_kod, test_kod
