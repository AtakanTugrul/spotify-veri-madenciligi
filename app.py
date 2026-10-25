"""Benzer şarkı bulucu — Streamlit demosu.

Yerelde çalıştırma:  streamlit run app.py
"""

import importlib
import os

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
from sklearn.decomposition import PCA

import src.arayuz
import src.oneri
import src.ozellikler
import src.veri


def _modulu_guncelle(modul) -> int:
    """Dosyası, yüklendiği andan sonra değişmiş bir modülü yeniden yükler; dosya sürümünü döndürür.

    Streamlit Cloud bir push'tan sonra app.py'yi yeni haliyle çalıştırır ama daha önce
    yüklenmiş src modüllerini bellekte eski halleriyle tutabiliyor. O durumda yeni kod eski
    modülde olmayan bir adı arar ve ImportError verir.
    """
    surum = os.stat(modul.__file__).st_mtime_ns
    if getattr(modul, "_dosya_surumu", None) != surum:
        importlib.reload(modul)
        modul._dosya_surumu = surum
    return surum


# Bağımlılık sırasıyla: önce veri/ozellikler, sonra onları içe aktaran oneri ve arayuz
KOD_SURUMU = tuple(_modulu_guncelle(m) for m in (src.veri, src.ozellikler, src.oneri, src.arayuz))

from src.arayuz import (ONERI_RENGI, RADAR_OZELLIKLERI, SORGU_RENGI, md_kacis, oneri_basligi,
                        oneri_karti, radar_svg, secili_sarki_karti, spotify_linki, svg_resim)
from src.oneri import DEMO_YOLU, BenzerSarkiBulucu

YOL_SINIRI = 50  # gezilen yolda tutulan en fazla şarkı (ekranda son 6'sı gösterilir)
ORNEKLER = ["Tarkan", "Ezhel", "Madrigal", "Sezen Aksu", "Bad Bunny", "Daft Punk"]
# Ses haritasında adı yazılan türler (birbirinden uzak, tanıdık türler)
HARITA_TURLERI = ["turkish", "metal", "classical", "sleep", "hip-hop", "latino", "techno",
                  "acoustic", "jazz", "comedy", "ambient", "punk"]

st.set_page_config(page_title="Ses İkizi · Benzer Şarkı Bulucu", page_icon="🎧", layout="wide")

st.html(f"""
<style>
  .block-container {{ max-width: 1180px; padding-top: 4.5rem; }}  /* Streamlit üst çubuğu ~3.75rem */
  .hero h1 {{ font-size: 2.6rem; font-weight: 800; letter-spacing: -0.02em; margin: 0; line-height: 1.1; }}
  .hero h1 span {{ background: linear-gradient(90deg, {SORGU_RENGI}, {ONERI_RENGI});
                   -webkit-background-clip: text; background-clip: text; color: transparent; }}
  .hero p {{ color: #9AA0AA; font-size: 1.05rem; max-width: 720px; margin: .6rem 0 1rem; }}
  .istatistikler {{ display: flex; gap: .6rem; flex-wrap: wrap; margin-bottom: .4rem; }}
  .istatistik {{ border: 1px solid #262B35; border-radius: 999px; padding: .3rem .85rem;
                 font-size: .85rem; color: #C9CDD3; background: #14171D; }}
  .istatistik b {{ color: #fff; }}
  .secili {{ border: 1px solid #262B35; border-radius: 18px; padding: 1.2rem 1.4rem;
             background: radial-gradient(120% 140% at 0% 0%, rgba(255,122,89,.14), transparent 55%), #14171D; }}
  .secili .etiket {{ color: {SORGU_RENGI}; font-size: .75rem; letter-spacing: .12em;
                     text-transform: uppercase; font-weight: 700; }}
  .secili h2 {{ margin: .2rem 0 0; padding: 0; font-size: 1.7rem; line-height: 1.2; }}
  .secili .sanatci {{ color: #C9CDD3; font-size: 1.05rem; margin-top: .15rem; }}
  .rakamlar {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: .6rem; margin-top: 1rem; }}
  .rakam {{ background: #0E1014; border: 1px solid #262B35; border-radius: 12px; padding: .55rem .7rem; }}
  .rakam .k {{ color: #9AA0AA; font-size: .72rem; text-transform: uppercase; letter-spacing: .08em; }}
  .rakam .v {{ font-size: 1.25rem; font-weight: 700; white-space: nowrap; }}
  .rakam .v small {{ font-size: .7rem; color: #9AA0AA; font-weight: 500; }}
  .radar-kutu {{ display: flex; justify-content: center; }}
  .radar-kutu img {{ max-width: 100%; height: auto; }}
  .lejant {{ display: flex; gap: 1rem; justify-content: center; color: #9AA0AA; font-size: .82rem; }}
  .lejant i {{ display: inline-block; width: 10px; height: 10px; border-radius: 3px; margin-right: .35rem; }}
  .kart {{ border: 1px solid #262B35; border-radius: 16px; padding: .95rem 1rem; background: #14171D;
           transition: border-color .15s, transform .15s; }}
  .kart:hover {{ border-color: {ONERI_RENGI}; transform: translateY(-2px); }}
  .kart-ust {{ display: flex; gap: .8rem; align-items: center; }}
  .sira {{ font-variant-numeric: tabular-nums; color: #5C6370; font-weight: 800; font-size: 1.3rem; width: 2rem; }}
  .kart-baslik {{ flex: 1; min-width: 0; }}
  .sarki-adi {{ font-weight: 700; font-size: 1.02rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
  .sarki-adi a {{ color: #E8EAED; text-decoration: none; }}
  .sarki-adi a:hover {{ color: {ONERI_RENGI}; }}
  .kart .sanatci {{ color: #9AA0AA; font-size: .9rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
  .mini-radar img {{ display: block; width: 88px; height: 88px; }}
  .metre {{ height: 6px; background: #232731; border-radius: 99px; margin-top: .75rem; overflow: hidden; }}
  .metre div {{ height: 100%; border-radius: 99px; background: linear-gradient(90deg, {SORGU_RENGI}, {ONERI_RENGI}); }}
  .metre-yazi {{ color: #9AA0AA; font-size: .82rem; margin-top: .35rem; }}
  .metre-yazi b {{ color: #E8EAED; }}
  .cipler {{ display: flex; flex-wrap: wrap; gap: .35rem; margin-top: .5rem; }}
  .cip {{ font-size: .75rem; padding: .12rem .55rem; border-radius: 999px; background: #1E222B; color: #B4BAC4; }}
  .cip-neden {{ background: rgba(61,214,198,.12); color: {ONERI_RENGI}; }}
  .cip-sessiz {{ background: transparent; border: 1px dashed #333946; color: #7D8490; }}
  .not {{ color: #7D8490; font-size: .82rem; }}
  .oneri-basligi {{ color: #C9CDD3; font-size: 1rem; margin: .2rem 0 .4rem; }}
  .oneri-basligi span {{ color: #9AA0AA; }}
  .kart {{ margin-bottom: -.35rem; }}
  @media (max-width: 640px) {{ .hero h1 {{ font-size: 2rem; }} }}
</style>
""")


@st.cache_resource(max_entries=1)
def bulucu_yukle(kod_surumu: tuple) -> BenzerSarkiBulucu:
    """Kod değişince (kod_surumu) eski sınıfın önbellekteki örneği yerine yenisi kurulur."""
    return BenzerSarkiBulucu(pd.read_csv(DEMO_YOLU))


@st.cache_data
def harita_verisi(kod_surumu: tuple) -> tuple[pd.DataFrame, pd.DataFrame, float]:
    """Tüm şarkıları PCA ile 2 boyuta indirir; şarkı koordinatlarını ve tür merkezlerini döndürür."""
    b = bulucu_yukle(kod_surumu)
    pca = PCA(n_components=2, random_state=42)
    koordinat = pca.fit_transform(b.X)
    tum = b.sarkilar[["track_id", "track_name", "artists", "turler"]].assign(
        x=koordinat[:, 0], y=koordinat[:, 1])
    tur_listesi = tum["turler"].str.split(", ")
    merkezler = pd.DataFrame([
        {"tur": t, **tum.loc[tur_listesi.map(lambda l: t in l), ["x", "y"]].median()}
        for t in HARITA_TURLERI])
    return tum, merkezler, float(pca.explained_variance_ratio_.sum())


def profil(satir: pd.Series) -> dict[str, float]:
    return {a: float(satir[a]) for a in RADAR_OZELLIKLERI}


def bin_ayrac(sayi: int) -> str:
    return f"{sayi:,}".replace(",", ".")


if not DEMO_YOLU.exists():
    st.error("Demo veri dosyası bulunamadı (data/demo_sarkilar.csv.gz). "
             "`python -m scripts.demo_verisi_hazirla` ile üretebilirsiniz.")
    st.stop()

bulucu = bulucu_yukle(KOD_SURUMU)
sarkilar = bulucu.sarkilar
tur_sayisi = sarkilar["turler"].str.split(", ").explode().nunique()

st.html(f"""
<div class="hero">
  <h1>Bu şarkının <span>ses ikizi</span> kim?</h1>
  <p>Bir şarkı seç; tür, dil ya da sanatçı bilgisine bakmadan, yalnızca <b>kulağa nasıl geldiğine</b>
  göre en yakın şarkıları bulalım. Sonuçlar bazen şaşırtıcı: Türkçe bir pop şarkısının ses ikizi
  Fransızca ya da Latin bir şarkı çıkabiliyor.</p>
  <div class="istatistikler">
    <div class="istatistik"><b>{bin_ayrac(len(sarkilar))}</b> şarkı</div>
    <div class="istatistik"><b>{tur_sayisi}</b> tür</div>
    <div class="istatistik"><b>9</b> ses özelliği</div>
    <div class="istatistik">içerik tabanlı · en yakın komşu</div>
  </div>
</div>
""")

with st.sidebar:
    st.subheader("Ayarlar")
    n = st.slider("Öneri sayısı", 4, 24, 8, step=2, key="oneri_sayisi")
    min_pop = st.slider("En az popülerlik", 0, 80, 20, key="min_pop",
                        help="Spotify popülerliği (0–100). Yükseltirseniz daha tanınır şarkılar gelir.")
    ayni_sanatci_haric = st.toggle("Aynı sanatçıyı hariç tut", value=True, key="ayni_sanatci_haric")
    st.divider()
    st.caption(
        "Veri: [Spotify Tracks Dataset](https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset) "
        "(Maharshi Pandya) · [ODbL](https://opendatacommons.org/licenses/odbl/1-0/). "
        "Ses özellikleri Spotify Web API'sinden alınmıştır. Bu demo Spotify ile ilişkili değildir."
    )


def sec(track_id: str, kaynak: str = "arama") -> None:
    """Bir şarkıyı seçilen şarkı yapar ve gezilen yola ekler.

    Yolda zaten olan bir şarkıya dönülürse yol oraya kadar kısaltılır (geri gitme).
    Seçim aramadan gelmediyse (öneri kartı, geri, yol) eski arama sonuçları
    kafa karıştırmasın diye arama kutusu temizlenir; karttan gelindiyse sayfa
    başa kaydırılır.
    """
    yol = st.session_state.yol
    yol = yol[:yol.index(track_id) + 1] if track_id in yol else yol + [track_id]
    st.session_state.yol = yol[-YOL_SINIRI:]
    st.session_state.secili = track_id
    st.session_state.yukari_kaydir = kaynak == "kart"
    if kaynak != "arama":
        st.session_state.arama = ""


def ornegi_uygula() -> None:
    ornek = st.session_state.ornek_secimi
    if ornek:
        st.session_state.arama = ornek
        sec(bulucu.ara(ornek, n=1)["track_id"].iloc[0])
        st.session_state.ornek_secimi = None  # hap düğmeler gibi davransın, seçili kalmasın


if "secili" not in st.session_state:
    st.session_state.arama = ORNEKLER[0]
    st.session_state.secili = bulucu.ara(ORNEKLER[0], n=1)["track_id"].iloc[0]
    st.session_state.yol = [st.session_state.secili]

arama_sol, arama_sag = st.columns([2, 3], vertical_alignment="bottom")
arama_sol.text_input("Şarkı veya sanatçı ara", key="arama", type="search", live="300ms",
                     placeholder="ör. simarik, maneskin, daft punk")
arama_sag.pills("Hızlı dene", ORNEKLER, key="ornek_secimi", on_change=ornegi_uygula)

adaylar = bulucu.ara(st.session_state.arama, n=6)
if st.session_state.arama.strip():
    if adaylar.empty:
        st.caption("Eşleşen şarkı bulunamadı. Başka bir ad ya da sanatçı deneyin.")
    else:
        with st.container(horizontal=True, gap="small", key="aday_listesi"):
            for aday in adaylar.itertuples():
                secili_mi = aday.track_id == st.session_state.secili
                st.button(md_kacis(f"{aday.track_name} — {aday.artists.replace(';', ', ')}"),
                          key=f"aday_{aday.track_id}", on_click=sec, args=(aday.track_id,),
                          type="primary" if secili_mi else "secondary", icon=":material/music_note:")

secim = st.session_state.secili
sorgu = bulucu.sarki(secim)
sonuc = bulucu.benzerler(secim, n=n, ayni_sanatci_haric=ayni_sanatci_haric, min_populerlik=min_pop)

if st.session_state.pop("yukari_kaydir", False):
    # Karttan yeni şarkıya geçilince sayfanın başındaki oynatıcıya dön (betik sabit, kullanıcı girdisi yok)
    st.html("""<script>
      setTimeout(() => {
        document.querySelectorAll('[data-testid="stMain"], [data-testid="stAppViewContainer"]')
          .forEach(e => e.scrollTo({top: 0, behavior: "smooth"}));
        window.scrollTo({top: 0, behavior: "smooth"});
      }, 80);
    </script>""", unsafe_allow_javascript=True)

yol = st.session_state.yol
if len(yol) > 1:
    with st.container(horizontal=True, gap="small", vertical_alignment="center", key="gezilen_yol"):
        st.button("Geri", key="geri", icon=":material/arrow_back:", on_click=sec, args=(yol[-2], "yol"))
        st.caption("Gezdiğin yol:", width="content")
        gosterilen = yol[-6:]
        if len(yol) > len(gosterilen):
            st.caption("…", width="content")
        for i, t in enumerate(gosterilen):
            if i:
                st.caption("→", width="content")
            st.button(md_kacis(bulucu.sarki(t)["track_name"]), key=f"yol_{t}", type="tertiary", on_click=sec, args=(t, "yol"),
                      disabled=t == secim)

st.write("")
sol, sag = st.columns([3, 2], gap="large")
with sol:
    st.html(secili_sarki_karti(sorgu.to_dict()))
    gomulu = spotify_linki(secim, embed=True)
    if gomulu:
        st.iframe(gomulu, height=152)

with sag:
    ortalama = profil(sonuc.mean(numeric_only=True)) if not sonuc.empty else None
    lejant = f'<span><i style="background:{SORGU_RENGI}"></i>Seçilen şarkı</span>'
    if ortalama:
        lejant += f'<span><i style="background:{ONERI_RENGI}"></i>Önerilerin ortalaması</span>'
    radar = svg_resim(radar_svg(profil(sorgu), ortalama, boyut=340), "Ses profili radar grafiği")
    st.html(f'<div class="radar-kutu">{radar}</div>'
            f'<div class="lejant">{lejant}</div>')

st.write("")
oneriler_sekmesi, harita_sekmesi, nasil_sekmesi = st.tabs(["Ses ikizleri", "Ses haritası", "Nasıl çalışıyor?"])

with oneriler_sekmesi:
    if sonuc.empty:
        st.info("Bu filtrelerle öneri kalmadı. En az popülerliği düşürmeyi deneyin.")
    else:
        st.html(oneri_basligi(sorgu.to_dict(), len(sonuc)))
        satirlar = sonuc.to_dict("records")
        for bas_i in range(0, len(satirlar), 3):
            for sutun, (i, satir) in zip(st.columns(3), enumerate(satirlar[bas_i:bas_i + 3], start=bas_i + 1)):
                with sutun:
                    st.html(oneri_karti(i, satir, profil(sorgu),
                                        bulucu.ortak_ozellikler(secim, satir["track_id"])))
                    st.button("Dinle ve ikizlerini bul", key=f"kart_{satir['track_id']}",
                              icon=":material/play_arrow:", width="stretch",
                              on_click=sec, args=(satir["track_id"], "kart"))
        st.html('<p class="not">Bir öneriye geçince o şarkı yukarıda çalınır ve onun ses ikizleri '
                'listelenir. Mini radarda turuncu seçilen şarkı, turkuaz öneri. ↑/↓ etiketleri iki '
                'şarkının <i>birlikte</i> belirgin şekilde yüksek/düşük olduğu özellikleri gösterir. '
                'Benzerlik %: rastgele bir şarkıya olan tipik uzaklığa göre ne kadar yakın.</p>')

with harita_sekmesi:
    tum, merkezler, aciklanan = harita_verisi(KOD_SURUMU)
    arka_plan = tum.sample(6000, random_state=0)
    vurgu = pd.concat([
        tum[tum["track_id"].isin(sonuc["track_id"])].assign(rol="Öneri"),
        tum[tum["track_id"] == secim].assign(rol="Seçilen şarkı"),
    ])
    eksen = alt.Axis(labels=False, ticks=False, title=None, grid=False, domain=False)
    olcek_x = alt.Scale(domain=list(np.percentile(tum["x"], [0.5, 99.5])))
    olcek_y = alt.Scale(domain=list(np.percentile(tum["y"], [0.5, 99.5])))
    taban = alt.Chart(arka_plan).mark_circle(size=12, opacity=0.45, color="#6B7280").encode(
        x=alt.X("x", axis=eksen, scale=olcek_x), y=alt.Y("y", axis=eksen, scale=olcek_y),
        tooltip=[alt.Tooltip("track_name", title="Şarkı"), alt.Tooltip("artists", title="Sanatçı")])
    tur_adlari = alt.Chart(merkezler).mark_text(fontSize=14, fontWeight="bold", color="#E8EAED",
                                                opacity=0.9).encode(x="x", y="y", text="tur")
    roller = alt.Scale(domain=["Seçilen şarkı", "Öneri"], range=[SORGU_RENGI, ONERI_RENGI])
    noktalar = alt.Chart(vurgu).mark_circle(stroke="#0E1014", strokeWidth=1.5, opacity=1).encode(
        x="x", y="y",
        color=alt.Color("rol", scale=roller, legend=alt.Legend(title=None, orient="top-left")),
        size=alt.Size("rol", scale=alt.Scale(domain=["Seçilen şarkı", "Öneri"], range=[260, 90]),
                      legend=None),
        tooltip=[alt.Tooltip("track_name", title="Şarkı"), alt.Tooltip("artists", title="Sanatçı"),
                 alt.Tooltip("turler", title="Türler")])
    st.altair_chart((taban + tur_adlari + noktalar).properties(height=520)
                    .configure_view(strokeWidth=0).configure(background="transparent"))
    st.html(f'<p class="not">Her gri nokta bir şarkı ({bin_ayrac(len(tum))} şarkıdan {bin_ayrac(len(arka_plan))} örnek). 9 ses özelliği PCA ile '
            f'2 boyuta indirildi; bu iki boyut farkın yalnızca %{100 * aciklanan:.0f}\'ini taşıyor. '
            'Bu yüzden 2B\'de biraz uzak görünen bir öneri, 9 boyutta aslında çok yakın olabilir. '
            'Tür adları o türdeki şarkıların merkezini gösterir.</p>')

with nasil_sekmesi:
    st.markdown(
        "1. Her şarkı 9 ses özelliğiyle bir nokta olarak temsil edilir: dans edilebilirlik, enerji, "
        "ses yüksekliği, konuşma, akustiklik, enstrümantallik, canlılık, mutluluk ve tempo.\n"
        "2. Özellikler ölçeklenir (ortalama 0, standart sapma 1). Böylece tempo (50–200 BPM) gibi "
        "geniş aralıklı özellikler uzaklığa hâkim olmaz.\n"
        "3. Seçilen şarkıya Öklid uzaklığı en küçük olan şarkılar listelenir. Aynı sanatçının "
        "şarkıları ve aynı şarkının farklı sürümleri hariç tutulur.\n\n"
        "**Ne kadar iyi?** Projedeki değerlendirmede önerilerin %11,5'i sorgu şarkısıyla aynı "
        "türden çıktı. Bu oran ölçekleme olmadan %6,8, rastgele seçimde %1. Ses benzerliği türü "
        "kısmen yakalıyor, ama dil ve kültür bilgisi ses özelliklerinde yok.\n\n"
        "Kod, analiz notebook'ları ve testler: "
        "[github.com/AtakanTugrul/spotify-veri-madenciligi](https://github.com/AtakanTugrul/spotify-veri-madenciligi)"
    )
