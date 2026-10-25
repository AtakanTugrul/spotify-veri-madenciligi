"""Streamlit demosunun HTML/SVG parçaları (radar grafiği, öneri kartları).

Şarkı ve sanatçı adları veri setinden gelir ve HTML'e gömülür; bu yüzden her
metin `html.escape` ile kaçışlanır.
"""

import base64
import math
import re
from html import escape

# Radarda gösterilen 0–1 aralıklı özellikler ve Türkçe adları
RADAR_OZELLIKLERI = {
    "danceability": "Dans",
    "energy": "Enerji",
    "valence": "Mutluluk",
    "acousticness": "Akustik",
    "instrumentalness": "Enstrümantal",
    "speechiness": "Konuşma",
    "liveness": "Canlılık",
}
OZELLIK_ADLARI = {
    **{"danceability": "dans edilebilirlik", "energy": "enerji", "valence": "mutluluk",
       "acousticness": "akustiklik", "instrumentalness": "enstrümantallik",
       "speechiness": "konuşma", "liveness": "canlı kayıt"},
    "loudness": "ses yüksekliği",
    "tempo": "tempo",
}
SORGU_RENGI = "#FF7A59"
ONERI_RENGI = "#3DD6C6"

_SPOTIFY_ID = re.compile(r"[A-Za-z0-9]{22}")


def spotify_linki(track_id: str, embed: bool = False) -> str | None:
    """Geçerli bir Spotify şarkı kimliği için link üretir; değilse None döner."""
    if not _SPOTIFY_ID.fullmatch(str(track_id)):
        return None
    yol = "embed/track" if embed else "track"
    return f"https://open.spotify.com/{yol}/{track_id}"


def _nokta(i: int, n: int, r: float, merkez: float) -> tuple[float, float]:
    aci = 2 * math.pi * i / n - math.pi / 2
    return merkez + r * math.cos(aci), merkez + r * math.sin(aci)


def _cokgen(degerler: list[float], yaricap: float, merkez: float) -> str:
    n = len(degerler)
    return " ".join("{:.1f},{:.1f}".format(*_nokta(i, n, yaricap * min(max(v, 0.0), 1.0), merkez))
                    for i, v in enumerate(degerler))


def radar_svg(sorgu: dict[str, float], oneri: dict[str, float] | None = None,
              boyut: int = 320, etiketli: bool = True) -> str:
    """0–1 aralıklı özellikleri radar (örümcek ağı) grafiği olarak çizer.

    `oneri` verilirse ikinci profil aynı grafiğe üst üste çizilir.
    """
    anahtarlar = list(RADAR_OZELLIKLERI)
    n = len(anahtarlar)
    pay = 74 if etiketli else 4
    merkez = boyut / 2
    yaricap = merkez - pay

    parcalar = [f'<svg viewBox="0 0 {boyut} {boyut}" width="{boyut}" height="{boyut}" '
                f'xmlns="http://www.w3.org/2000/svg" font-family="Helvetica, Arial, sans-serif">']
    for oran in (0.25, 0.5, 0.75, 1.0):
        parcalar.append(f'<polygon points="{_cokgen([oran] * n, yaricap, merkez)}" '
                        'fill="none" stroke="#2C313C" stroke-width="1"/>')
    for i in range(n):
        x, y = _nokta(i, n, yaricap, merkez)
        parcalar.append(f'<line x1="{merkez}" y1="{merkez}" x2="{x:.1f}" y2="{y:.1f}" '
                        'stroke="#2C313C" stroke-width="1"/>')

    profiller = [(sorgu, SORGU_RENGI)] + ([(oneri, ONERI_RENGI)] if oneri else [])
    for profil, renk in profiller:
        noktalar = _cokgen([float(profil[a]) for a in anahtarlar], yaricap, merkez)
        parcalar.append(f'<polygon points="{noktalar}" fill="{renk}" fill-opacity="0.22" '
                        f'stroke="{renk}" stroke-width="{2 if etiketli else 1.5}" '
                        'stroke-linejoin="round"/>')

    if etiketli:
        for i, a in enumerate(anahtarlar):
            x, y = _nokta(i, n, yaricap + 16, merkez)
            hiza = "middle" if abs(x - merkez) < 5 else ("start" if x > merkez else "end")
            parcalar.append(f'<text x="{x:.1f}" y="{y + 4:.1f}" text-anchor="{hiza}" '
                            f'fill="#9AA0AA" font-size="12">{RADAR_OZELLIKLERI[a]}</text>')
    parcalar.append("</svg>")
    return "".join(parcalar)


def svg_resim(svg: str, aciklama: str) -> str:
    """SVG'yi <img> olarak gömer (Streamlit'in st.html'i satır içi SVG'yi temizliyor)."""
    veri = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f'<img src="data:image/svg+xml;base64,{veri}" alt="{escape(aciklama)}">'


def neden_cipleri(ortaklar: list[tuple[str, int]]) -> str:
    """("energy", 1) → "↑ enerji" gibi küçük etiketler."""
    if not ortaklar:
        return '<span class="cip cip-sessiz">dengeli, ortalamaya yakın profil</span>'
    return "".join(
        f'<span class="cip cip-neden" title="İkisinde de belirgin şekilde '
        f'{"yüksek" if yon > 0 else "düşük"}">{"↑" if yon > 0 else "↓"} {OZELLIK_ADLARI[o]}</span>'
        for o, yon in ortaklar)


def secili_sarki_karti(sarki: dict) -> str:
    """Seçilen şarkının kartı: ad, sanatçı, türler ve tempo/popülerlik/ses yüksekliği."""
    turler = "".join(f'<span class="cip">{escape(t.strip())}</span>'
                     for t in str(sarki["turler"]).split(","))
    return f"""
<div class="secili">
  <div class="etiket">Seçilen şarkı</div>
  <h2>{escape(str(sarki["track_name"]))}</h2>
  <div class="sanatci">{escape(str(sarki["artists"]).replace(";", ", "))}</div>
  <div class="cipler">{turler}</div>
  <div class="rakamlar">
    <div class="rakam"><div class="k">Tempo</div><div class="v">{float(sarki["tempo"]):.0f}<small> BPM</small></div></div>
    <div class="rakam"><div class="k">Popülerlik</div><div class="v">{int(sarki["popularity"])}</div></div>
    <div class="rakam"><div class="k">Ses</div><div class="v">{float(sarki["loudness"]):.1f}<small> dB</small></div></div>
  </div>
</div>"""


def oneri_basligi(sarki: dict, adet: int) -> str:
    """Önerilerin hangi şarkıya göre yapıldığını söyleyen başlık."""
    ad = escape(str(sarki["track_name"]))
    sanatci = escape(str(sarki["artists"]).replace(";", ", "))
    return (f'<p class="oneri-basligi"><b>{ad}</b> <span>({sanatci})</span> ile ses olarak '
            f'en çok benzeşen {adet} şarkı</p>')


def oneri_karti(sira: int, sarki: dict, sorgu_profili: dict[str, float],
                ortaklar: list[tuple[str, int]]) -> str:
    """Tek bir öneriyi kart olarak çizer: ad, sanatçı, benzerlik, türler, nedenler, mini radar."""
    ad = escape(str(sarki["track_name"]))
    sanatci = escape(str(sarki["artists"]).replace(";", ", "))
    link = spotify_linki(sarki["track_id"])
    baslik = (f'<a href="{link}" target="_blank" rel="noopener noreferrer">{ad}</a>'
              if link else ad)
    yuzde = round(100 * float(sarki["benzerlik"]))
    turler = "".join(f'<span class="cip">{escape(t.strip())}</span>'
                     for t in str(sarki["turler"]).split(",")[:3])
    mini = svg_resim(radar_svg(sorgu_profili, {a: sarki[a] for a in RADAR_OZELLIKLERI},
                               boyut=88, etiketli=False), "Seçilen şarkı ile önerinin ses profili")
    return f"""
<div class="kart">
  <div class="kart-ust">
    <div class="sira">{sira:02d}</div>
    <div class="kart-baslik">
      <div class="sarki-adi">{baslik}</div>
      <div class="sanatci">{sanatci}</div>
    </div>
    <div class="mini-radar">{mini}</div>
  </div>
  <div class="metre"><div style="width:{yuzde}%"></div></div>
  <div class="metre-yazi"><b>%{yuzde}</b> benzer · popülerlik {int(sarki["popularity"])}</div>
  <div class="cipler">{neden_cipleri(ortaklar)}</div>
  <div class="cipler">{turler}</div>
</div>"""
