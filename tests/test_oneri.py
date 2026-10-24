import pytest

from conftest import sarki
from src.oneri import BenzerSarkiBulucu


@pytest.fixture
def bulucu(tablo):
    return BenzerSarkiBulucu(tablo(
        sarki("sorgu", artists="Tarkan", track_name="Şımarık", popularity=66, danceability=0.8, energy=0.8),
        sarki("ikiz", artists="Karan Aujla", track_name="Adhiya", popularity=58, danceability=0.79, energy=0.81),
        sarki("ayni_sanatci", artists="Tarkan", track_name="Kuzu Kuzu", popularity=60, danceability=0.8, energy=0.8),
        sarki("featuring", artists="Ezhel;Tarkan", track_name="Ortak", popularity=55, danceability=0.8, energy=0.8),
        sarki("az_populer", artists="X", track_name="Gizli", popularity=5, danceability=0.75, energy=0.75),
        sarki("uzak", artists="Y", track_name="Ninni", popularity=50, danceability=0.1, energy=0.1),
        sarki("orta", artists="Z", track_name="Orta", popularity=50, danceability=0.5, energy=0.5),
    ))


def test_sarkinin_kendisi_onerilmez(bulucu):
    sonuc = bulucu.benzerler("sorgu", n=10, ayni_sanatci_haric=False)
    assert "sorgu" not in sonuc["track_id"].tolist()


def test_en_yakin_sarki_once_gelir_ve_uzakliklar_artan_sirada(bulucu):
    sonuc = bulucu.benzerler("sorgu", n=10)
    assert sonuc["track_id"].iloc[0] == "ikiz"
    assert sonuc["uzaklik"].is_monotonic_increasing
    assert sonuc["track_id"].iloc[-1] == "uzak"


def test_ayni_sanatci_ve_ortak_calismalar_haric_tutulur(bulucu):
    sonuc = bulucu.benzerler("sorgu", n=10)
    assert not {"ayni_sanatci", "featuring"} & set(sonuc["track_id"])


def test_ayni_sanatci_filtresi_kapatilabilir(bulucu):
    sonuc = bulucu.benzerler("sorgu", n=10, ayni_sanatci_haric=False)
    assert {"ayni_sanatci", "featuring"} <= set(sonuc["track_id"])


def test_min_populerlik_filtresi(bulucu):
    sonuc = bulucu.benzerler("sorgu", n=10, min_populerlik=40)
    assert "az_populer" not in sonuc["track_id"].tolist()
    assert (sonuc["popularity"] >= 40).all()


def test_n_sonuc_sayisini_sinirlar(bulucu):
    assert len(bulucu.benzerler("sorgu", n=2)) == 2


def test_olcekleme_genis_aralikli_ozelligin_baskin_olmasini_engeller(tablo):
    # "tempo_farkli" yalnızca tempoda 10 BPM farklı; "ses_farkli" ise iki ses
    # özelliğinde belirgin farklı. Ölçekleme olmasaydı ham 10 BPM'lik fark
    # 0.3'lük farklardan çok daha büyük görünür ve sıralama ters dönerdi.
    satirlar = [sarki("sorgu", artists="S", tempo=120.0),
                sarki("tempo_farkli", artists="T", tempo=130.0),
                sarki("ses_farkli", artists="U", danceability=0.8, energy=0.8)]
    satirlar += [sarki(f"dolgu{i}", artists=f"D{i}", tempo=60.0 + 15 * i) for i in range(8)]
    bulucu = BenzerSarkiBulucu(tablo(*satirlar))
    sonuc = bulucu.benzerler("sorgu", n=20)["track_id"].tolist()
    assert sonuc.index("tempo_farkli") < sonuc.index("ses_farkli")


def test_ara_ad_ve_sanatcida_buyuk_kucuk_harfe_duyarsiz_arar(bulucu):
    assert bulucu.ara("şımarık")["track_id"].tolist() == ["sorgu"]
    assert set(bulucu.ara("TARKAN")["track_id"]) == {"sorgu", "ayni_sanatci", "featuring"}


def test_ara_sonuclari_populerlige_gore_siralar(bulucu):
    assert bulucu.ara("tarkan")["track_id"].tolist() == ["sorgu", "ayni_sanatci", "featuring"]


def test_ara_bos_metinde_bos_doner(bulucu):
    assert bulucu.ara("   ").empty


def test_ara_ozel_karakterleri_duz_metin_olarak_arar(bulucu):
    assert bulucu.ara("(").empty  # regex olarak yorumlansaydı hata verirdi


def test_bilinmeyen_sarki_anlasilir_hata_verir(bulucu):
    with pytest.raises(KeyError, match="bulunamadı"):
        bulucu.benzerler("yok")


def test_tekrarlayan_track_id_reddedilir(tablo):
    with pytest.raises(ValueError, match="tekil_sarkilar"):
        BenzerSarkiBulucu(tablo(sarki("t1"), sarki("t1", genre="dance")))
