"""Veri yükleme ve temizleme fonksiyonları (tüm notebook'lar bunları kullanır)."""

from pathlib import Path

import pandas as pd

PROJE_KOKU = Path(__file__).resolve().parent.parent
VERI_YOLU = PROJE_KOKU / "data" / "dataset.csv"

# Şarkının "sesini" tarif eden sayısal özellikler
SES_OZELLIKLERI = [
    "danceability",
    "energy",
    "loudness",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
    "tempo",
]


def veri_yukle(yol: Path = VERI_YOLU) -> pd.DataFrame:
    """Ham CSV'yi okur. İlk sütun yalnızca satır numarası olduğu için indeks yapılır."""
    if not Path(yol).exists():
        raise FileNotFoundError(
            f"{yol} bulunamadı. Veriyi Kaggle'dan indirip data/dataset.csv olarak kaydedin."
        )
    return pd.read_csv(yol, index_col=0)


def temizle(df: pd.DataFrame) -> pd.DataFrame:
    """Tür düzeyinde analiz için temizlenmiş veri.

    - Sanatçı/albüm/şarkı adı eksik satırları atar.
    - Tamamen aynı olan tekrar satırları atar.
    - Süresi 0 olan ya da tempo/ölçü bilgisi 0 olan (ölçülememiş) şarkıları atar.

    Aynı şarkı birden fazla türde yer alabilir; bu satırlar korunur çünkü
    her biri farklı bir türü temsil eder. Şarkı düzeyinde analiz için
    `tekil_sarkilar` kullanılır.
    """
    df = df.dropna(subset=["artists", "album_name", "track_name"])
    df = df.drop_duplicates()
    df = df[(df["duration_ms"] > 0) & (df["tempo"] > 0) & (df["time_signature"] > 0)]
    return df.reset_index(drop=True)


def tekil_sarkilar(df: pd.DataFrame) -> pd.DataFrame:
    """Her track_id'den yalnızca bir satır bırakır (şarkı düzeyinde analiz için)."""
    return df.drop_duplicates(subset="track_id").reset_index(drop=True)
