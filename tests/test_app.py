"""Demo için duman testi: uygulama repodaki küçük veri dosyasıyla hatasız açılıyor mu?

Streamlit'in kendi test aracı (AppTest) uygulamayı tarayıcı ve sunucu olmadan çalıştırır.
"""

import pytest

from src.oneri import DEMO_YOLU

AppTest = pytest.importorskip("streamlit.testing.v1").AppTest
APP = str(DEMO_YOLU.parent.parent / "app.py")

pytestmark = pytest.mark.skipif(not DEMO_YOLU.exists(), reason="demo veri dosyası yok")


@pytest.fixture(scope="module")
def uygulama():
    at = AppTest.from_file(APP, default_timeout=120).run()
    assert not at.exception, at.exception
    return at


def test_acilista_ornek_sarki_secili_ve_oneriler_gosteriliyor(uygulama):
    assert uygulama.text_input[0].value == "Tarkan"
    assert uygulama.selectbox[0].value is not None
    assert not uygulama.info  # "öneri kalmadı" uyarısı yok


def test_eslesmeyen_aramada_bilgi_mesaji_gosteriliyor(uygulama):
    uygulama.text_input[0].set_value("zzzqqq-boyle-bir-sarki-yok").run()
    assert not uygulama.exception
    assert "bulunamadı" in uygulama.info[0].value


def test_filtreler_degisince_uygulama_hatasiz_calisiyor(uygulama):
    uygulama.text_input[0].set_value("Daft Punk").run()
    uygulama.slider(key="min_pop").set_value(80).run()
    uygulama.toggle(key="ayni_sanatci_haric").set_value(False).run()
    assert not uygulama.exception


def test_veri_dosyasi_yoksa_okunur_hata_gosteriliyor(monkeypatch, tmp_path):
    # app.py, DEMO_YOLU'nu her çalıştırmada src.oneri'den okur; yolu var olmayan bir dosyaya çeviriyoruz
    monkeypatch.setattr("src.oneri.DEMO_YOLU", tmp_path / "yok.csv.gz")
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception
    assert "bulunamadı" in at.error[0].value
    assert not at.selectbox  # uygulama hata mesajından sonra durdu
