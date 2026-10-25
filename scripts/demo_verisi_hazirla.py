"""Ham Kaggle CSV'sinden Streamlit demosunun kullandığı veri dosyasını üretir.

Çalıştırma (proje kökünden):  python -m scripts.demo_verisi_hazirla
"""

from src.oneri import DEMO_YOLU, demo_tablosu
from src.veri import temizle, veri_yukle

if __name__ == "__main__":
    tablo = demo_tablosu(temizle(veri_yukle()))
    tablo.to_csv(DEMO_YOLU, index=False, compression="gzip")
    print(f"{len(tablo):,} şarkı → {DEMO_YOLU} ({DEMO_YOLU.stat().st_size / 1e6:.1f} MB)")
