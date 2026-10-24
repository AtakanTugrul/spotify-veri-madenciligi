import numpy as np
import pandas as pd
import pytest

from conftest import sarki
from src.ozellikler import ana_sanatci, sanatci_kodla, surumleri_birlestir


# --- surumleri_birlestir -----------------------------------------------------

def test_surumler_birlestirilince_en_populer_surum_kalir(tablo):
    df = tablo(
        sarki("derleme", artists="Tarkan", track_name="Şımarık", popularity=0),
        sarki("orijinal", artists="Tarkan", track_name="Şımarık", popularity=66),
        sarki("baska", artists="Tarkan", track_name="Kuzu Kuzu", popularity=40),
    )
    sonuc = surumleri_birlestir(df)
    assert sorted(sonuc["track_id"]) == ["baska", "orijinal"]


def test_surum_eslesmesi_buyuk_kucuk_harf_ve_bosluga_duyarsiz(tablo):
    df = tablo(
        sarki("a", artists="Queen", track_name="Bohemian Rhapsody", popularity=75),
        sarki("b", artists=" queen", track_name="BOHEMIAN RHAPSODY ", popularity=10),
    )
    assert surumleri_birlestir(df)["track_id"].tolist() == ["a"]


def test_farkli_sanatcilarin_ayni_adli_sarkilari_birlesmez(tablo):
    df = tablo(
        sarki("a", artists="Queen", track_name="Bohemian Rhapsody"),
        sarki("b", artists="Hayseed Dixie", track_name="Bohemian Rhapsody"),
    )
    assert len(surumleri_birlestir(df)) == 2


# --- ana_sanatci -------------------------------------------------------------

def test_ana_sanatci_ilk_sanatciyi_alir(tablo):
    df = tablo(sarki("a", artists="Artz;Şehinşah;Ceg"), sarki("b", artists="Ezhel"))
    assert ana_sanatci(df).tolist() == ["Artz", "Ezhel"]


# --- sanatci_kodla: sızıntı testleri ------------------------------------------

def _veri(rng, n=200, sanatci_sayisi=20):
    return pd.DataFrame({
        "ana_sanatci": rng.choice([f"s{i}" for i in range(sanatci_sayisi)], n),
        "popularity": rng.integers(0, 100, n).astype(float),
    })


def test_test_kodlamasi_test_populerligine_bagli_degil():
    rng = np.random.default_rng(0)
    egitim, test = _veri(rng), _veri(rng, n=50)
    _, once = sanatci_kodla(egitim, test)

    test_degismis = test.assign(popularity=rng.integers(0, 100, len(test)).astype(float))
    _, sonra = sanatci_kodla(egitim, test_degismis)
    np.testing.assert_array_equal(once, sonra)


@pytest.mark.parametrize("satir", [0, 17, 199])
def test_egitim_satirinin_kendi_populerligi_kendi_kodlamasina_karismaz(satir):
    """Out-of-fold kodlamanın amacı: bir şarkının kendi hedef değeri değişse bile
    kendi özelliği değişmemeli. Değişiyorsa model cevabı görüyor demektir."""
    rng = np.random.default_rng(1)
    egitim, test = _veri(rng), _veri(rng, n=10)
    once, _ = sanatci_kodla(egitim, test)

    degismis = egitim.copy()
    degismis.loc[satir, "popularity"] += 1000
    sonra, _ = sanatci_kodla(degismis, test)
    assert sonra[satir] == pytest.approx(once[satir])


def test_hic_gorulmemis_sanatci_genel_ortalamayi_alir():
    egitim = pd.DataFrame({"ana_sanatci": ["a", "a", "b"], "popularity": [10.0, 20.0, 60.0]})
    test = pd.DataFrame({"ana_sanatci": ["yeni"], "popularity": [99.0]})
    _, test_kod = sanatci_kodla(egitim, test, kat_sayisi=3)
    assert test_kod[0] == pytest.approx(30.0)


def test_yumusatma_az_sarkili_sanatciyi_genel_ortalamaya_ceker():
    egitim = pd.DataFrame({
        "ana_sanatci": ["cok"] * 50 + ["az"] + ["diger"] * 49,
        "popularity": [90.0] * 50 + [90.0] + [10.0] * 49,
    })
    test = pd.DataFrame({"ana_sanatci": ["cok", "az"], "popularity": [0.0, 0.0]})
    _, (cok, az) = sanatci_kodla(egitim, test, m=5)
    genel = egitim["popularity"].mean()
    assert az < cok                      # tek şarkılık sanatçıya daha az güvenilir
    assert genel < az < 90               # ama genel ortalamadan yukarıda
    assert cok == pytest.approx((50 * 90 + 5 * genel) / 55)
