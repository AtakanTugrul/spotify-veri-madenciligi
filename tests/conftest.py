"""Testler gerçek veri setine ihtiyaç duymaz; küçük, elle kurulmuş tablolar kullanır.
Böylece veri dosyası olmayan ortamlarda (ör. GitHub Actions) da çalışırlar."""

import pandas as pd
import pytest

from src.veri import SES_OZELLIKLERI


def sarki(track_id, artists="A", track_name=None, popularity=50, genre="pop", **ozellik):
    """Varsayılan değerlerle tek bir şarkı satırı üretir; istenen alanlar ezilebilir."""
    satir = {
        "track_id": track_id,
        "artists": artists,
        "album_name": "Albüm",
        "track_name": track_name if track_name is not None else f"Şarkı {track_id}",
        "popularity": popularity,
        "duration_ms": 200_000,
        "explicit": False,
        "key": 5,
        "mode": 1,
        "time_signature": 4,
        "track_genre": genre,
    }
    satir.update({o: 0.5 for o in SES_OZELLIKLERI})
    satir.update({"loudness": -8.0, "tempo": 120.0})
    satir.update(ozellik)
    return satir


@pytest.fixture
def tablo():
    def _tablo(*satirlar):
        return pd.DataFrame(list(satirlar))
    return _tablo
