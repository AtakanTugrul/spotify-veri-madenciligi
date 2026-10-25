"""Benzer şarkı bulucu — Streamlit demosu.

Yerelde çalıştırma:  streamlit run app.py
"""

import pandas as pd
import streamlit as st

from src.oneri import DEMO_YOLU, BenzerSarkiBulucu

# Grafikte gösterilen 0–1 aralıklı özellikler (tempo ve ses yüksekliği farklı ölçekte)
GRAFIK_OZELLIKLERI = {
    "danceability": "Dans edilebilirlik",
    "energy": "Enerji",
    "valence": "Mutluluk",
    "acousticness": "Akustiklik",
    "instrumentalness": "Enstrümantallik",
    "speechiness": "Konuşma",
    "liveness": "Canlı kayıt",
}
ORNEKLER = ["Tarkan", "Ezhel", "Madrigal", "Bad Bunny", "Daft Punk"]

st.set_page_config(page_title="Benzer Şarkı Bulucu", page_icon="🎵", layout="wide")


@st.cache_resource
def bulucu_yukle() -> BenzerSarkiBulucu:
    return BenzerSarkiBulucu(pd.read_csv(DEMO_YOLU))


def etiket(satir: pd.Series) -> str:
    return f"{satir.track_name} — {satir.artists.replace(';', ', ')}"


st.title("🎵 Benzer Şarkı Bulucu")
st.caption(
    "Bir şarkı seçin; 81 bin şarkı arasından **ses olarak** en yakınlarını bulalım. "
    "Benzerlik yalnızca Spotify ses özelliklerine (dans edilebilirlik, enerji, mutluluk, "
    "tempo…) dayanır: tür, dil veya sanatçı bilgisi kullanılmaz."
)

bulucu = bulucu_yukle()

with st.sidebar:
    st.header("Ayarlar")
    n = st.slider("Öneri sayısı", 5, 30, 10)
    min_pop = st.slider("En az popülerlik", 0, 80, 20,
                        help="Spotify popülerliği (0–100). Yükseltirseniz daha tanınır şarkılar gelir.")
    ayni_sanatci_haric = st.checkbox("Aynı sanatçıyı hariç tut", value=True)
    st.divider()
    st.markdown(
        "Veri: [Spotify Tracks Dataset](https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset) "
        "(Maharshi Pandya), [ODbL](https://opendatacommons.org/licenses/odbl/1-0/). "
        "Ses özellikleri Spotify Web API'sinden alınmıştır."
    )

if "arama" not in st.session_state:
    st.session_state.arama = ORNEKLER[0]
st.text_input("Şarkı veya sanatçı ara", key="arama")
sutunlar = st.columns(len(ORNEKLER))
for sutun, ornek in zip(sutunlar, ORNEKLER):
    sutun.button(ornek, width="stretch",
                 on_click=lambda o=ornek: st.session_state.update(arama=o))

adaylar = bulucu.ara(st.session_state.arama, n=30)
if adaylar.empty:
    st.info("Eşleşen şarkı bulunamadı. Başka bir ad veya sanatçı deneyin.")
    st.stop()

secim = st.selectbox("Şarkı", adaylar["track_id"].tolist(),
                     format_func=lambda t: etiket(adaylar.set_index("track_id").loc[t]))
sorgu = adaylar.set_index("track_id").loc[secim]
sonuc = bulucu.benzerler(secim, n=n, ayni_sanatci_haric=ayni_sanatci_haric,
                         min_populerlik=min_pop)

sol, sag = st.columns([3, 2], gap="large")
with sol:
    st.subheader("Ses olarak en yakın şarkılar")
    if sonuc.empty:
        st.info("Bu filtrelerle öneri kalmadı. En az popülerliği düşürmeyi deneyin.")
    else:
        tablo = pd.DataFrame({
            "Şarkı": sonuc["track_name"],
            "Sanatçı": sonuc["artists"].str.replace(";", ", "),
            "Türler": sonuc["turler"],
            "Popülerlik": sonuc["popularity"],
            "Uzaklık": sonuc["uzaklik"],
            "Spotify": "https://open.spotify.com/track/" + sonuc["track_id"],
        })
        st.dataframe(
            tablo, hide_index=True, width="stretch",
            column_config={
                "Popülerlik": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%d"),
                "Uzaklık": st.column_config.NumberColumn(format="%.2f",
                                                         help="Ölçeklenmiş ses uzayında uzaklık; küçük = daha benzer"),
                "Spotify": st.column_config.LinkColumn(display_text="Dinle ↗"),
            },
        )

with sag:
    st.subheader("Ses profili")
    st.caption(f"**{etiket(sorgu)}** · türler: {sorgu.turler} · "
               f"{sorgu.tempo:.0f} BPM")
    profil = pd.DataFrame({"Seçilen şarkı": sorgu[list(GRAFIK_OZELLIKLERI)].astype(float)})
    if not sonuc.empty:
        profil["Önerilerin ortalaması"] = sonuc[list(GRAFIK_OZELLIKLERI)].mean()
    profil.index = list(GRAFIK_OZELLIKLERI.values())
    st.bar_chart(profil, horizontal=True, stack=False, height=360)

with st.expander("Nasıl çalışıyor?"):
    st.markdown(
        "1. Her şarkı 9 ses özelliğiyle bir nokta olarak temsil edilir.\n"
        "2. Özellikler ölçeklenir (ortalama 0, standart sapma 1); böylece tempo gibi "
        "geniş aralıklı özellikler uzaklığa hâkim olmaz.\n"
        "3. Seçilen şarkıya Öklid uzaklığı en küçük olan şarkılar listelenir.\n\n"
        "Projedeki değerlendirmede önerilerin %11,5'i sorgu şarkısıyla aynı türden çıktı "
        "(rastgele seçimde %1). Ses benzerliği türü kısmen yakalıyor; dil ve kültür "
        "bilgisi ses özelliklerinde yok. Bu yüzden Türkçe bir şarkıya Fransızca veya "
        "Latin bir öneri gelmesi şaşırtıcı değil."
    )
