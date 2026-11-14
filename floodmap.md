# Combined flood-susceptibility evidence

Storms: 81 (big storms with an hour ≥ 0.50" at the Mint: 7: 2012-12-02, 2014-12-02, 2014-12-03, 2014-12-11, 2019-02-13, 2022-12-31, 2024-02-20).

Terrain grid: 2048×2048 pixels (~9 m).
Land cells: 5764
SFPUC zone: 1 polygons from https://data.sfgov.org/resource/jzu3-4yxp.geojson

## Does terrain or the SFPUC zone predict where flooding gets reported?

Share of land cells with any report in a big storm: 19.9%.

| Group | Cells | Share with a big-storm report | vs. citywide |
|---|---|---|---|
| Bowls: lowest 10% topographic position | 577 | 25.8% | 1.3× |
| Ridges: highest 50% topographic position | 2882 | 16.2% | 0.8× |
| Large drainage: top 5% upslope area | 289 | 29.4% | 1.5× |
| Small drainage: bottom 50% upslope area | 2884 | 14.9% | 0.7× |
| In SFPUC 100-year zone | 524 | 36.5% | 1.8× |
| Outside SFPUC zone | 5240 | 18.2% | 0.9× |
| SFPUC zone AND bowl (lowest 25%) | 177 | 40.1% | 2.0× |

## Classes

| Class | Cells |
|---|---|
| A: modeled + observed | 165 |
| B: modeled, little reported | 509 |
| C: reported, not a low spot (drain problems) | 492 |
| D: neither | 4598 |

## Check spots

| Spot | Class | In SFPUC zone | Topo position (m) | Upslope area (km²) | Storms with reports (all / big) |
|---|---|---|---|---|---|
| 17th & Folsom | A: modeled + observed | yes | -6.1 | 0.01 | 9 / 5 |
| West Portal (Ulloa & Vicente) | D: neither | no | -13.9 | 0.13 | 5 / 1 |
| SoMa (6th & Folsom) | A: modeled + observed | yes | -4.6 | 0.01 | 19 / 4 |
| Mission Bay (16th & 3rd) | D: neither | no | -0.4 | 0.00 | 3 / 1 |
| Bayview (3rd & Evans) | A: modeled + observed | yes | -3.1 | 0.01 | 12 / 4 |
| Twin Peaks (hilltop) | D: neither | no | 42.9 | 0.01 | 3 / 0 |
| Hayes Valley (Fell & Divisadero) | C: reported, not a low spot (drain problems) | no | -12.8 | 0.05 | 12 / 5 |

## Top class-A cells (modeled + observed), by big-storm evidence

| Cell | Big storms with reports | All storms | Flood reports in big storms | Topo position (m) | Upslope (km²) |
|---|---|---|---|---|---|
| 37.7850, -122.4330 | 6 | 19 | 11 | -14.7 | 0.09 |
| 37.7685, -122.4150 | 6 | 17 | 6 | -5.7 | 0.01 |
| 37.7790, -122.4030 | 5 | 24 | 13 | -4.9 | 0.01 |
| 37.7640, -122.4150 | 5 | 9 | 9 | -4.6 | 0.02 |
| 37.7505, -122.4300 | 5 | 14 | 7 | -19.6 | 0.23 |
| 37.7625, -122.4150 | 5 | 9 | 7 | -6.1 | 0.01 |
| 37.7670, -122.4165 | 5 | 6 | 6 | -5.0 | 0.17 |
| 37.7760, -122.4195 | 5 | 13 | 3 | -2.0 | 0.02 |
| 37.7775, -122.4045 | 4 | 19 | 8 | -4.6 | 0.01 |
| 37.7700, -122.4120 | 4 | 12 | 8 | -3.5 | 0.01 |
| 37.7715, -122.4015 | 4 | 7 | 8 | -2.3 | 0.01 |
| 37.7670, -122.4195 | 4 | 9 | 7 | -5.4 | 0.04 |
| 37.7805, -122.4225 | 4 | 28 | 6 | -6.6 | 0.04 |
| 37.7730, -122.4420 | 4 | 9 | 6 | -14.3 | 0.05 |
| 37.7370, -122.4705 | 4 | 14 | 5 | -15.9 | 0.05 |
| 37.7940, -122.3985 | 4 | 9 | 5 | -3.2 | 0.07 |
| 37.7790, -122.4015 | 4 | 9 | 5 | -3.7 | 0.01 |
| 37.7430, -122.3880 | 4 | 12 | 4 | -3.1 | 0.01 |
| 37.7505, -122.4390 | 4 | 8 | 4 | -37.4 | 0.08 |
| 37.7610, -122.4645 | 4 | 10 | 3 | -26.8 | 0.10 |
(basemap: © OpenStreetMap contributors © CARTO)
