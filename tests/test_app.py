"""Demo için duman testleri: uygulama repodaki veri dosyasıyla hatasız açılıyor ve
arama → seçim → öneriden öneriye geçiş akışı çalışıyor mu?

Streamlit'in kendi test aracı (AppTest) uygulamayı tarayıcı ve sunucu olmadan çalıştırır.
"""

import pandas as pd
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


def _html_metinleri(at):
    return [h.proto.body for h in at.get("html")]


def test_karttan_geciste_sayfa_basina_kaydirma_betigi_bir_kez_eklenir():
    at = _ac()
    assert not any("scrollTo" in h for h in _html_metinleri(at))
    _dugmeler(at, "kart_")[0].click().run()
    assert sum("scrollTo" in h for h in _html_metinleri(at)) == 1
    at.slider(key="min_pop").set_value(30).run()  # başka bir etkileşimde betik tekrar eklenmez
    assert not any("scrollTo" in h for h in _html_metinleri(at))


def test_hizli_dene_dugmesi_aramayi_ve_secimi_degistirir():
    at = _ac()
    at.button_group(key="ornek_secimi").set_value("Ezhel").run()
    assert not at.exception
    assert at.text_input(key="arama").value == "Ezhel"
    assert len(at.session_state.yol) == 2
    secili_kart = [h for h in _html_metinleri(at) if h.lstrip().startswith('<div class="secili">')]
    assert len(secili_kart) == 1 and "Ezhel" in secili_kart[0]
    assert at.button_group(key="ornek_secimi").value is None  # düğme seçili kalmaz


def _yolda_olmayan_oneriye_gec(at):
    yeni = [k for k in _dugmeler(at, "kart_") if k.key.removeprefix("kart_") not in at.session_state.yol]
    yeni[0].click().run()


def test_uzun_yol_kisaltilarak_gosterilir():
    at = _ac()
    for _ in range(7):
        _yolda_olmayan_oneriye_gec(at)
    assert not at.exception
    assert len(at.session_state.yol) == 8
    assert any(c.value == "…" for c in at.caption)      # ekranda yalnızca son 6 şarkı
    assert len(_dugmeler(at, "yol_")) == 6


def test_yol_sinirdan_uzun_tutulmaz():
    at = _ac()
    secili = at.session_state.secili
    gercek = [t for t in pd.read_csv(DEMO_YOLU, usecols=["track_id"])["track_id"].head(80) if t != secili]
    at.session_state.yol = gercek[:60] + [secili]
    _yolda_olmayan_oneriye_gec(at)
    assert not at.exception
    assert len(at.session_state.yol) == 50
    assert len(_dugmeler(at, "yol_")) == 6


def test_veri_dosyasi_yoksa_okunur_hata_gosteriliyor(monkeypatch, tmp_path):
    # app.py, DEMO_YOLU'nu her çalıştırmada src.oneri'den okur; yolu var olmayan bir dosyaya çeviriyoruz.
    # Önce bir kez çalıştırıyoruz ki modül sürümleri kaydedilsin ve uygulama src.oneri'yi yeniden
    # yükleyip yamayı silmesin.
    _ac()
    monkeypatch.setattr("src.oneri.DEMO_YOLU", tmp_path / "yok.csv.gz")
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception
    assert "bulunamadı" in at.error[0].value
    assert not _dugmeler(at, "kart_")  # uygulama hata mesajından sonra durdu


def test_bellekte_kalmis_eski_modul_kendiliginden_yenilenir(monkeypatch):
    """Streamlit Cloud bir push'tan sonra app.py'yi yeni haliyle çalıştırır ama daha önce
    yüklenmiş src modüllerini eski halleriyle bellekte tutabilir. Bunu taklit ediyoruz: yeni
    eklenmiş bir fonksiyonu modülden siliyoruz (eski sürümde yokmuş gibi). Uygulama, dosyanın
    değiştiğini fark edip modülü yeniden yüklemeli; ImportError vermemeli."""
    import src.arayuz

    _ac()  # modüller bir kez yüklensin ve sürümleri kaydedilsin
    monkeypatch.delattr(src.arayuz, "md_kacis")
    monkeypatch.delattr(src.arayuz, "_dosya_surumu", raising=False)  # canlıdaki gibi: sürümü hiç kaydedilmemiş
    at = AppTest.from_file(APP, default_timeout=120).run()
    assert not at.exception, at.exception
    assert hasattr(src.arayuz, "md_kacis")


def test_degisen_modulu_ice_aktaran_moduller_de_yenilenir(monkeypatch):
    """Yalnızca src/veri.py değişse bile, ondan `from ... import` ile ad alan src/oneri.py
    da yenilenmeli; yoksa oneri eski adlara bağlı kalır."""
    import src.oneri
    import src.veri

    _ac()
    monkeypatch.setattr(src.veri, "_dosya_surumu", -1)  # yalnızca veri.py "değişti"
    monkeypatch.delattr(src.oneri, "sadelestir")       # oneri'nin eski hali taklidi
    at = AppTest.from_file(APP, default_timeout=120).run()
    assert not at.exception, at.exception
    assert hasattr(src.oneri, "sadelestir")
