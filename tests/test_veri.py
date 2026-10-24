import pandas as pd
import pytest

from conftest import sarki
from src.veri import temizle, tekil_sarkilar, veri_yukle


def test_temizle_eksik_isimli_satiri_atar(tablo):
    df = tablo(sarki("t1"), {**sarki("t2"), "track_name": None})
    assert temizle(df)["track_id"].tolist() == ["t1"]


def test_temizle_tamamen_ayni_satirlari_teke_indirir(tablo):
    df = tablo(sarki("t1"), sarki("t1"), sarki("t2"))
    assert temizle(df)["track_id"].tolist() == ["t1", "t2"]


@pytest.mark.parametrize("alan", ["duration_ms", "tempo", "time_signature"])
def test_temizle_olculememis_sarkilari_atar(tablo, alan):
    df = tablo(sarki("t1"), sarki("t2", **{alan: 0}))
    assert temizle(df)["track_id"].tolist() == ["t1"]


def test_temizle_farkli_turlerdeki_ayni_sarkiyi_korur(tablo):
    # Aynı şarkı iki türün listesinde: tür düzeyi analiz için iki satır da kalmalı
    df = tablo(sarki("t1", genre="pop"), sarki("t1", genre="dance"))
    assert sorted(temizle(df)["track_genre"]) == ["dance", "pop"]


def test_tekil_sarkilar_her_sarkidan_bir_tane_birakir(tablo):
    df = tablo(sarki("t1", genre="pop"), sarki("t1", genre="dance"), sarki("t2"))
    sonuc = tekil_sarkilar(df)
    assert sonuc["track_id"].tolist() == ["t1", "t2"]
    assert sonuc.index.tolist() == [0, 1]


def test_veri_yukle_dosya_yoksa_anlasilir_hata_verir(tmp_path):
    with pytest.raises(FileNotFoundError, match="Kaggle"):
        veri_yukle(tmp_path / "yok.csv")


def test_veri_yukle_ilk_sutunu_indeks_yapar(tmp_path, tablo):
    yol = tmp_path / "dataset.csv"
    tablo(sarki("t1"), sarki("t2")).to_csv(yol)  # pandas indeksi ilk sütun olarak yazar
    df = veri_yukle(yol)
    assert "Unnamed: 0" not in df.columns
    assert df["track_id"].tolist() == ["t1", "t2"]
    pd.testing.assert_index_equal(df.index, pd.RangeIndex(2))
