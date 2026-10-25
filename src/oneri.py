"""Ses özelliklerine göre benzer şarkı bulucu (notebook ve Streamlit demosu kullanır)."""

import unicodedata

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from src.ozellikler import surumleri_birlestir
from src.veri import PROJE_KOKU, SES_OZELLIKLERI, tekil_sarkilar


DEMO_YOLU = PROJE_KOKU / "data" / "demo_sarkilar.csv.gz"
DEMO_SUTUNLARI = ["track_id", "track_name", "artists", "popularity", "turler"] + SES_OZELLIKLERI


def demo_tablosu(temiz: pd.DataFrame) -> pd.DataFrame:
    """Streamlit demosu için şarkı düzeyinde, yeniden paylaşılabilir bir tablo üretir.

    `temiz` tür düzeyindeki veridir (`temizle` çıktısı). Her şarkının yer aldığı
    tüm türler `turler` sütununda birleştirilir, sürümler birleştirilir ve yalnızca
    bulucunun ihtiyaç duyduğu sütunlar tutulur.
    """
    turler = (temiz.groupby("track_id")["track_genre"]
                   .agg(lambda t: ", ".join(sorted(set(t)))).rename("turler"))
    sarkilar = surumleri_birlestir(tekil_sarkilar(temiz)).join(turler, on="track_id")
    return sarkilar[DEMO_SUTUNLARI].round({o: 4 for o in SES_OZELLIKLERI})


# Ayrıştırmayla (NFKD) sadeleşmeyen harfler elle eşlenir; Türkçe I/İ/ı'nın hepsi "i" olur
_OZEL_HARFLER = str.maketrans({"ı": "i", "I": "i", "İ": "i", "ø": "o", "Ø": "o", "æ": "ae", "Æ": "ae",
                               "œ": "oe", "Œ": "oe", "ß": "ss", "đ": "d", "Đ": "d", "ł": "l", "Ł": "l"})


def sadelestir(metin: str) -> str:
    """Aramada kullanılan sade biçim: küçük harf, harf işaretleri yok, tek boşluk.

    "Måneskin" → "maneskin", "ŞIMARIK" → "simarik", "Beyoncé" → "beyonce".
    """
    ayrik = unicodedata.normalize("NFKD", str(metin).translate(_OZEL_HARFLER))
    isaretsiz = "".join(h for h in ayrik if not unicodedata.combining(h))
    return " ".join(isaretsiz.casefold().split())


def _sanatcilar(metin: str) -> set[str]:
    return {s.strip().lower() for s in str(metin).split(";") if s.strip()}


class BenzerSarkiBulucu:
    """Şarkıları ölçeklenmiş ses özellikleri uzayında Öklid uzaklığıyla karşılaştırır.

    Her özellik ortalaması 0, standart sapması 1 olacak şekilde ölçeklenir;
    böylece tempo (50–200) gibi geniş aralıklı özellikler uzaklığa hâkim olmaz.
    """

    def __init__(self, sarkilar: pd.DataFrame, ozellikler: list[str] = SES_OZELLIKLERI):
        self.ozellikler = list(ozellikler)
        self.sarkilar = sarkilar.reset_index(drop=True)
        self.olcekleyici = StandardScaler()
        self.X = self.olcekleyici.fit_transform(self.sarkilar[self.ozellikler])
        self._konum = pd.Series(self.sarkilar.index, index=self.sarkilar["track_id"])
        self._sade_ad = self.sarkilar["track_name"].map(sadelestir)
        self._sade_sanatci = self.sarkilar["artists"].map(sadelestir)
        if self._konum.index.duplicated().any():
            raise ValueError("Her track_id yalnızca bir kez geçmeli (önce tekil_sarkilar kullanın).")

    def ara(self, metin: str, n: int = 10) -> pd.DataFrame:
        """Şarkı adında veya sanatçıda `metin` geçen şarkıları popülerliğe göre sıralar.

        Büyük/küçük harfe ve harf işaretlerine duyarsızdır: "maneskin" Måneskin'i,
        "simarik" Şımarık'ı bulur.
        """
        metin = sadelestir(metin)
        if not metin:
            return self.sarkilar.iloc[0:0]
        eslesme = (self._sade_ad.str.contains(metin, regex=False)
                   | self._sade_sanatci.str.contains(metin, regex=False))
        return self.sarkilar[eslesme].nlargest(n, "popularity")

    def sarki(self, track_id: str) -> pd.Series:
        """Tek bir şarkının satırı; bilinmeyen kimlikte KeyError."""
        if track_id not in self._konum.index:
            raise KeyError(f"Şarkı bulunamadı: {track_id}")
        return self.sarkilar.iloc[self._konum[track_id]]

    def benzerler(self, track_id: str, n: int = 10, ayni_sanatci_haric: bool = True,
                  min_populerlik: int = 0) -> pd.DataFrame:
        """`track_id` şarkısına ses olarak en yakın `n` şarkıyı döndürür.

        - Şarkının kendisi her zaman hariç tutulur.
        - `ayni_sanatci_haric`: sorgu şarkısıyla ortak sanatçısı olanlar hariç tutulur
          (yoksa liste aynı sanatçının şarkılarıyla dolabilir).
        - `min_populerlik`: daha tanınır öneriler için alt popülerlik sınırı.
        """
        if track_id not in self._konum.index:
            raise KeyError(f"Şarkı bulunamadı: {track_id}")
        i = self._konum[track_id]
        uzaklik = np.linalg.norm(self.X - self.X[i], axis=1)

        aday = np.ones(len(self.sarkilar), dtype=bool)
        aday[i] = False
        if min_populerlik > 0:
            aday &= (self.sarkilar["popularity"] >= min_populerlik).to_numpy()
        if ayni_sanatci_haric:
            sorgu = _sanatcilar(self.sarkilar.at[i, "artists"])
            aday &= ~self.sarkilar["artists"].map(lambda a: bool(_sanatcilar(a) & sorgu)).to_numpy()

        secilen = np.flatnonzero(aday)
        en_yakin = secilen[np.argsort(uzaklik[secilen], kind="stable")[:n]]
        # Benzerlik: rastgele bir şarkıya olan tipik (medyan) uzaklığa göre ne kadar yakın
        benzerlik = np.clip(1 - uzaklik[en_yakin] / np.median(uzaklik), 0, 1)
        return self.sarkilar.iloc[en_yakin].assign(uzaklik=uzaklik[en_yakin], benzerlik=benzerlik)

    def ortak_ozellikler(self, track_id: str, diger_id: str, esik: float = 0.75,
                         en_fazla: int = 3) -> list[tuple[str, int]]:
        """İki şarkının birlikte belirgin şekilde yüksek (+1) ya da düşük (-1) olduğu
        özellikleri, en belirgin olandan başlayarak döndürür ("neden benziyor?").

        Belirginlik ölçeklenmiş değerle ölçülür: ikisi de ortalamadan en az `esik`
        standart sapma uzakta ve aynı yönde olmalı.
        """
        a, b = (self.X[self._konum[t]] for t in (track_id, diger_id))
        ortak = (np.sign(a) == np.sign(b)) & (np.abs(a) >= esik) & (np.abs(b) >= esik)
        guc = np.minimum(np.abs(a), np.abs(b))
        sira = [i for i in np.argsort(-guc, kind="stable") if ortak[i]][:en_fazla]
        return [(self.ozellikler[i], int(np.sign(a[i]))) for i in sira]
