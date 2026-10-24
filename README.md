# Spotify Veri Madenciliği

~114 bin Spotify şarkısının ses özellikleri (dans edilebilirlik, enerji, mutluluk, tempo…) üzerinde veri madenciliği projesi.

> 🚧 Çalışma devam ediyor. Bulgular ve grafikler proje ilerledikçe eklenecek.

## Sorular

1. Müzik türleri ses özellikleriyle gerçekten ayrışıyor mu?
2. Şarkılar doğal "çalma listesi" gruplarına ayrılabilir mi? (kümeleme)
3. Bir şarkının popülerliği ses özelliklerinden tahmin edilebilir mi?
4. Türk müziği dünyadan ses olarak nasıl ayrışıyor, en yakın benzerleri hangileri?
5. Benzer şarkı bulucu: bir şarkı ver, ses olarak en yakın 10 şarkıyı bul.

## Veri

[Spotify Tracks Dataset](https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset) — Maharshi Pandya, Kaggle.
Lisans: veritabanı [Open Database License (ODbL)](https://opendatacommons.org/licenses/odbl/1-0/), içerik (şarkı/sanatçı bilgileri) © ilgili hak sahipleri. Ses özellikleri Spotify Web API'sinden alınmıştır.

Veri bu repoda yer almaz. Çalıştırmak için CSV dosyasını Kaggle'dan indirip `data/dataset.csv` olarak kaydedin.

## Kurulum

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Proje yapısı

```
data/        Veri (repoda yok, Kaggle'dan indirilir)
notebooks/   Analiz notebook'ları
src/         Tekrar kullanılan Python kodu
tests/       Testler
figures/     Kaydedilen grafikler
```
