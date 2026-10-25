# Veri lisansı

`demo_sarkilar.csv.gz`, [Spotify Tracks Dataset](https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset)
(Maharshi Pandya, Kaggle) veri setinden türetilmiş bir veritabanıdır.

- Bu türetilmiş veritabanı, orijinali gibi [Open Database License (ODbL) 1.0](https://opendatacommons.org/licenses/odbl/1-0/)
  ile lisanslanmıştır. Bu dosyayı kullanan ya da paylaşan herkes ODbL şartlarına uymalıdır.
- İçerik (şarkı ve sanatçı adları) © ilgili hak sahipleri. Ses özellikleri Spotify Web API'sinden alınmıştır.
- Repodaki kod ayrı olarak lisanslanır; bu dosya yalnızca veri için geçerlidir.

## Orijinalden farkları

`scripts/demo_verisi_hazirla.py` ile üretilir:

1. Adı eksik, tekrar eden ve ölçülememiş (süre/tempo/ölçü 0) satırlar atıldı.
2. Her şarkı tek satıra indirildi; şarkının yer aldığı türler `turler` sütununda birleştirildi.
3. Aynı sanatçının aynı adlı sürümlerinden yalnızca en popüleri bırakıldı.
4. Yalnızca şu sütunlar tutuldu: track_id, track_name, artists, popularity, turler ve 9 ses özelliği
   (ses özellikleri 4 ondalığa yuvarlandı).
