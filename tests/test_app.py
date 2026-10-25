"""Demo için duman testleri: uygulama repodaki veri dosyasıyla hatasız açılıyor ve
arama → seçim → öneriden öneriye geçiş akışı çalışıyor mu?

Streamlit'in kendi test aracı (AppTest) uygulamayı tarayıcı ve sunucu olmadan çalıştırır.
"""

import pytest

from src.oneri import DEMO_YOLU

AppTest = pytest.importorskip("streamlit.testing.v1").AppTest
APP = str(DEMO_YOLU.parent.parent / "app.py")

pytestmark = pytest.mark.skipif(not DEMO_YOLU.exists(), reason="demo veri dosyası yok")


def _ac():
    at = AppTest.from_file(APP, default_timeout=120).run()
    assert not at.exception, at.exception
    return at


def _dugmeler(at, onek):
    return [b for b in at.button if b.key and b.key.startswith(onek)]


@pytest.fixture(scope="module")
def uygulama():
    return _ac()


def test_acilista_ornek_sarki_secili_ve_oneri_kartlari_var(uygulama):
    assert uygulama.text_input(key="arama").value == "Tarkan"
    secili = uygulama.session_state.secili
    assert uygulama.session_state.yol == [secili]
    assert len(_dugmeler(uygulama, "kart_")) == 8  # varsayılan öneri sayısı
    assert not _dugmeler(uygulama, "geri")         # tek şarkı varken geri düğmesi yok


def test_eslesmeyen_aramada_mesaj_gosterilir_secim_korunur(uygulama):
    once = uygulama.session_state.secili
    uygulama.text_input(key="arama").set_value("zzzqqq-boyle-bir-sarki-yok").run()
    assert not uygulama.exception
    assert any("bulunamadı" in c.value for c in uygulama.caption)
    assert uygulama.session_state.secili == once
    assert _dugmeler(uygulama, "kart_")  # öneriler hâlâ gösteriliyor


def test_filtreler_degisince_uygulama_hatasiz_calisiyor(uygulama):
    uygulama.text_input(key="arama").set_value("Daft Punk").run()
    uygulama.slider(key="min_pop").set_value(80).run()
    uygulama.toggle(key="ayni_sanatci_haric").set_value(False).run()
    assert not uygulama.exception


def test_harf_isaretsiz_arama_oneri_dugmesiyle_secilir():
    at = _ac()
    at.text_input(key="arama").set_value("maneskin").run()
    adaylar = _dugmeler(at, "aday_")
    assert adaylar and all("Måneskin" in b.label for b in adaylar)
    adaylar[0].click().run()
    assert not at.exception
    assert at.session_state.secili == adaylar[0].key.removeprefix("aday_")


def test_karttan_gecis_ve_geri_donus():
    at = _ac()
    ilk = at.session_state.secili
    kart = _dugmeler(at, "kart_")[0]
    hedef = kart.key.removeprefix("kart_")

    kart.click().run()
    assert not at.exception
    assert at.session_state.secili == hedef
    assert at.session_state.yol == [ilk, hedef]
    assert "yukari_kaydir" not in at.session_state  # kaydırma işareti bir kez kullanılıp silinir
    assert at.text_input(key="arama").value == ""     # eski arama sonuçları gösterilmez
    assert not _dugmeler(at, "aday_")

    _dugmeler(at, "geri")[0].click().run()
    assert at.session_state.secili == ilk
    assert at.session_state.yol == [ilk]


def test_gezilen_yoldaki_sarkiya_tiklayinca_yol_kisalir():
    at = _ac()
    ilk = at.session_state.secili
    for _ in range(2):  # yolda olmayan bir öneriye geç (öneri listesi seçili şarkıya geri dönebilir)
        yeni = [k for k in _dugmeler(at, "kart_") if k.key.removeprefix("kart_") not in at.session_state.yol]
        yeni[0].click().run()
    assert len(at.session_state.yol) == 3

    at.button(key=f"yol_{ilk}").click().run()
    assert not at.exception
    assert at.session_state.yol == [ilk]


def test_yoldaki_bir_sarki_oneri_olarak_secilirse_yol_oraya_kisalir():
    at = _ac()
    ilk = at.session_state.secili
    _dugmeler(at, "kart_")[0].click().run()
    geri_donus = at.button(key=f"kart_{ilk}") if f"kart_{ilk}" in [b.key for b in at.button] else None
    if geri_donus is None:
        pytest.skip("ilk şarkı bu veride ikinci şarkının önerileri arasında değil")
    geri_donus.click().run()
    assert at.session_state.yol == [ilk]


def test_veri_dosyasi_yoksa_okunur_hata_gosteriliyor(monkeypatch, tmp_path):
    # app.py, DEMO_YOLU'nu her çalıştırmada src.oneri'den okur; yolu var olmayan bir dosyaya çeviriyoruz
    monkeypatch.setattr("src.oneri.DEMO_YOLU", tmp_path / "yok.csv.gz")
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception
    assert "bulunamadı" in at.error[0].value
    assert not _dugmeler(at, "kart_")  # uygulama hata mesajından sonra durdu
