"""block_cells keeps native values in a fixed window around the block's nearest cell."""
import numpy as np

from bench import grib
from bench.settings import CELLS_HALF, LAT, LON


class FakeMsg:
    def __init__(self):
        la = np.linspace(LAT - 0.2, LAT + 0.2, 41)[:, None] * np.ones((1, 41))
        lo = np.ones((41, 1)) * np.linspace(LON - 0.2, LON + 0.2, 41)[None, :]
        self._ll = (la, lo + 360)                         # GRIB longitudes are often 0-360
        self.values = np.arange(41 * 41, dtype=float).reshape(41, 41)
        self.meta = {"gridType": "fake", "latitudeOfFirstGridPointInDegrees": 1, "longitudeOfFirstGridPointInDegrees": 2, "units": "kg m-2"}

    def latlons(self):
        return self._ll

    def __getitem__(self, k):
        return self.meta[k]

    def has_key(self, k):
        return k in self.meta


def test_block_cells_native_window():
    out = grib.block_cells(FakeMsg())
    b = out["block_cell"]
    assert (b["row"], b["col"]) == (20, 20) and b["value"] == 20 * 41 + 20
    v = out["cells"]["values"]
    n = 2 * CELLS_HALF + 1
    assert len(v) == n and len(v[0]) == n and v[CELLS_HALF][CELLS_HALF] == b["value"]
    assert out["units"] == "kg m-2"
