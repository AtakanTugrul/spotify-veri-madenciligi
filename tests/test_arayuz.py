import base64

from src.arayuz import (RADAR_OZELLIKLERI, neden_cipleri, oneri_karti, radar_svg, spotify_linki,
                        svg_resim)

PROFIL = {a: 0.5 for a in RADAR_OZELLIKLERI}


def _oneri(**alan):
    sarki = {"track_id": "4uLU6hMCjMI75M1A2tKUQC", "track_name": "Şarkı", "artists": "A;B",
             "popularity": 58, "turler": "pop, turkish", "benzerlik": 0.873, **PROFIL}
    sarki.update(alan)
    return sarki


def test_spotify_linki_yalnizca_gecerli_kimlik_icin_uretilir():
    assert spotify_linki("4uLU6hMCjMI75M1A2tKUQC") == "https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC"
    assert spotify_linki("4uLU6hMCjMI75M1A2tKUQC", embed=True).endswith("/embed/track/4uLU6hMCjMI75M1A2tKUQC")
    assert spotify_linki("x/../../evil") is None
    assert spotify_linki('4uLU6hMCjMI75M1A2tKUQ"') is None


def test_kart_sarki_ve_sanatci_adini_kacislar():
    kart = oneri_karti(1, _oneri(track_name="<script>alert(1)</script>", artists='"><img src=x>'),
                       PROFIL, [])
    assert "<script>" not in kart and "<img src=x>" not in kart
    assert "&lt;script&gt;" in kart


def test_kart_benzerlik_yuzdesi_ve_sanatcilari_gosterir():
    kart = oneri_karti(3, _oneri(), PROFIL, [("energy", 1)])
    assert "%87" in kart and "A, B" in kart and ">03<" in kart
    assert "↑ enerji" in kart


def test_gecersiz_kimlikte_link_verilmez():
    assert "href" not in oneri_karti(1, _oneri(track_id="bozuk"), PROFIL, [])


def test_neden_cipleri_bos_listede_aciklama_verir():
    assert "dengeli" in neden_cipleri([])
    assert "↓ akustiklik" in neden_cipleri([("acousticness", -1)])


def test_radar_ikinci_profili_ve_etiketleri_cizer():
    tek = radar_svg(PROFIL)
    cift = radar_svg(PROFIL, {a: 1.0 for a in RADAR_OZELLIKLERI}, etiketli=False)
    assert tek.count("fill-opacity") == 1 and cift.count("fill-opacity") == 2
    assert "Enerji" in tek and "Enerji" not in cift


def test_radar_araligin_disindaki_degerleri_kirpar():
    asiri = radar_svg({a: 5.0 for a in RADAR_OZELLIKLERI}, boyut=100, etiketli=False)
    tam = radar_svg({a: 1.0 for a in RADAR_OZELLIKLERI}, boyut=100, etiketli=False)
    assert asiri == tam


def test_svg_resim_svgyi_base64_img_olarak_gomer():
    svg = radar_svg(PROFIL, boyut=100)
    img = svg_resim(svg, 'a"b')
    assert img.startswith('<img src="data:image/svg+xml;base64,')
    veri = img.split("base64,")[1].split('"')[0]
    assert base64.b64decode(veri).decode() == svg
    assert 'alt="a&quot;b"' in img
