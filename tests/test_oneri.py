import pytest

from conftest import sarki
from src.oneri import BenzerSarkiBulucu, sadelestir


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


def test_demo_tablosu_turleri_birlestirir_ve_surumleri_teke_indirir(tablo):
    from src.oneri import DEMO_SUTUNLARI, demo_tablosu
    temiz = tablo(
        sarki("t1", artists="Tarkan", track_name="Şımarık", popularity=66, genre="turkish"),
        sarki("t1", artists="Tarkan", track_name="Şımarık", popularity=66, genre="pop"),
        sarki("derleme", artists="Tarkan", track_name="Şımarık", popularity=0, genre="dance"),
        sarki("t2", artists="Ezhel", popularity=50, danceability=0.123456),
    )
    sonuc = demo_tablosu(temiz)
    assert list(sonuc.columns) == DEMO_SUTUNLARI
    assert sorted(sonuc["track_id"]) == ["t1", "t2"]
    assert sonuc.set_index("track_id").at["t1", "turler"] == "pop, turkish"
    assert sonuc.set_index("track_id").at["t2", "danceability"] == 0.1235


def test_benzerlik_sifir_bir_arasinda_ve_uzaklikla_ters_sirali(bulucu):
    sonuc = bulucu.benzerler("sorgu", n=10)
    assert sonuc["benzerlik"].between(0, 1).all()
    assert sonuc["benzerlik"].is_monotonic_decreasing


def test_ortak_ozellikler_ayni_yonde_belirgin_olanlari_verir(tablo):
    satirlar = [sarki("a", artists="A", energy=0.9, acousticness=0.1, valence=0.9),
                sarki("b", artists="B", energy=0.9, acousticness=0.1, valence=0.1)]
    satirlar += [sarki(f"d{i}", artists=f"D{i}", energy=0.4, acousticness=0.6, valence=0.5)
                 for i in range(8)]
    bulucu = BenzerSarkiBulucu(tablo(*satirlar))
    sonuc = dict(bulucu.ortak_ozellikler("a", "b"))
    assert sonuc == {"energy": 1, "acousticness": -1}  # valence zıt yönde: sayılmaz


def test_ortak_ozellikler_en_fazla_sinirini_uygular(tablo):
    satirlar = [sarki(c, artists=c, energy=0.9, acousticness=0.1, valence=0.9) for c in "ab"]
    satirlar += [sarki(f"d{i}", artists=f"D{i}") for i in range(8)]
    bulucu = BenzerSarkiBulucu(tablo(*satirlar))
    assert len(bulucu.ortak_ozellikler("a", "b", en_fazla=2)) == 2


def test_filtreler_herkesi_elerse_bos_sonuc_doner(bulucu):
    sonuc = bulucu.benzerler("sorgu", n=10, min_populerlik=100)
    assert sonuc.empty
    assert {"uzaklik", "benzerlik"} <= set(sonuc.columns)



@pytest.mark.parametrize("ham, sade", [
    ("Måneskin", "maneskin"),
    ("ŞIMARIK", "simarik"),
    ("Şımarık", "simarik"),
    ("İstanbul", "istanbul"),
    ("Beyoncé", "beyonce"),
    ("Røyksopp", "royksopp"),
    ("Straße", "strasse"),
    ("Sigur Rós Ágætis byrjun", "sigur ros agaetis byrjun"),
    ("Þórður Guðmundsson", "thordur gudmundsson"),
    ("Ħal Tarxien Ŧ", "hal tarxien t"),
    ("  Sezen   Aksu ", "sezen aksu"),
])
def test_sadelestir_harf_isaretlerini_ve_buyuk_harfi_kaldirir(ham, sade):
    assert sadelestir(ham) == sade


@pytest.mark.parametrize("sorgu", ["maneskin", "MANESKIN", "Måneskin", "beggin"])
def test_ara_harf_isaretlerine_duyarsiz(tablo, sorgu):
    bulucu = BenzerSarkiBulucu(tablo(
        sarki("m", artists="Måneskin", track_name="Beggin'"),
        sarki("t", artists="Tarkan", track_name="Şımarık"),
    ))
    assert bulucu.ara(sorgu)["track_id"].tolist() == ["m"]


def test_ara_turkce_karakter_yazmadan_bulur(bulucu):
    assert bulucu.ara("simarik")["track_id"].tolist() == ["sorgu"]
    assert bulucu.ara("SIMARIK")["track_id"].tolist() == ["sorgu"]


def test_sarki_satiri_dondurur_bilinmeyende_hata_verir(bulucu):
    assert bulucu.sarki("ikiz")["track_name"] == "Adhiya"
    with pytest.raises(KeyError, match="bulunamadı"):
        bulucu.sarki("yok")
