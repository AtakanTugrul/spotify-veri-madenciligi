"""Ses özelliklerine göre benzer şarkı bulucu (notebook ve Streamlit demosu kullanır)."""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from src.veri import SES_OZELLIKLERI


def _sanatcilar(metin: str) -> set[str]:
    return {s.strip().lower() for s in str(metin).split(";") if s.strip()}


class BenzerSarkiBulucu:
    """Şarkıları ölçeklenmiş ses özellikleri uzayında Öklid uzaklığıyla karşılaştırır.

    Her özellik ortalaması 0, standart sapması 1 olacak şekilde ölçeklenir;
    böylece tempo (50–200) gibi geniş aralıklı özellikler uzaklığa hâkim olmaz.
    """

    def __init__(self, sarkilar: pd.DataFrame, ozellikler: list[str] = SES_OZELLIKLERI):
        self.ozellikler = list(ozellikler)
        self.sarkilar = sarkilar.reset_index(drop=True)
        self.olcekleyici = StandardScaler()
        self.X = self.olcekleyici.fit_transform(self.sarkilar[self.ozellikler])
        self._konum = pd.Series(self.sarkilar.index, index=self.sarkilar["track_id"])
        if self._konum.index.duplicated().any():
            raise ValueError("Her track_id yalnızca bir kez geçmeli (önce tekil_sarkilar kullanın).")

    def ara(self, metin: str, n: int = 10) -> pd.DataFrame:
        """Şarkı adında veya sanatçıda `metin` geçen şarkıları popülerliğe göre sıralar."""
        metin = metin.strip().lower()
        if not metin:
            return self.sarkilar.iloc[0:0]
        eslesme = (self.sarkilar["track_name"].str.lower().str.contains(metin, regex=False)
                   | self.sarkilar["artists"].str.lower().str.contains(metin, regex=False))
        return self.sarkilar[eslesme].nlargest(n, "popularity")

    def benzerler(self, track_id: str, n: int = 10, ayni_sanatci_haric: bool = True,
                  min_populerlik: int = 0) -> pd.DataFrame:
        """`track_id` şarkısına ses olarak en yakın `n` şarkıyı döndürür.

        - Şarkının kendisi her zaman hariç tutulur.
        - `ayni_sanatci_haric`: sorgu şarkısıyla ortak sanatçısı olanlar hariç tutulur
          (yoksa liste aynı sanatçının şarkılarıyla dolabilir).
        - `min_populerlik`: daha tanınır öneriler için alt popülerlik sınırı.
        """
        if track_id not in self._konum.index:
            raise KeyError(f"Şarkı bulunamadı: {track_id}")
        i = self._konum[track_id]
        uzaklik = np.linalg.norm(self.X - self.X[i], axis=1)

        aday = np.ones(len(self.sarkilar), dtype=bool)
        aday[i] = False
        if min_populerlik > 0:
            aday &= (self.sarkilar["popularity"] >= min_populerlik).to_numpy()
        if ayni_sanatci_haric:
            sorgu = _sanatcilar(self.sarkilar.at[i, "artists"])
            aday &= ~self.sarkilar["artists"].map(lambda a: bool(_sanatcilar(a) & sorgu)).to_numpy()

        secilen = np.flatnonzero(aday)
        en_yakin = secilen[np.argsort(uzaklik[secilen], kind="stable")[:n]]
        return self.sarkilar.iloc[en_yakin].assign(uzaklik=uzaklik[en_yakin])
