# External benchmarking: direct access probe

Run at 2026-11-25 16:41 UTC from GitHub Actions.

## NWS gridpoints (point forecast QPF)

```
{
 "points": 200,
 "grid": "MTR 85,105",
 "gridpoints": 200,
 "updateTime": "2026-11-25T10:07:49+00:00",
 "qpf_periods": 33,
 "qpf_first": [
  {
   "validTime": "2026-11-25T04:00:00+00:00/PT2H",
   "value": 2.032
  },
  {
   "validTime": "2026-11-25T06:00:00+00:00/PT6H",
   "value": 13.97
  },
  {
   "validTime": "2026-11-25T12:00:00+00:00/PT6H",
   "value": 0
  }
 ],
 "qpf_durations": [
  "PT2H",
  "PT6H"
 ],
 "pop_periods": 41
}
```

## WPC QPF / ERO

```
{
 "wpc 6h qpf dir": {
  "status": 200,
  "sample": [
   "p48m_2026112500f168.grb",
   "p48m_2026112512f120.grb",
   "p48m_2026112512f168.grb",
   "p48m_2026112600f120.grb",
   "p48m_2026112600f168.grb",
   "p120m_2026112312f120.grb",
   "p120m_2026112400f120.grb",
   "p120m_2026112412f120.grb",
   "p120m_2026112500f120.grb",
   "p120m_2026112512f120.grb",
   "p168m_2026112312f168.grb",
   "p168m_2026112400f168.grb",
   "p168m_2026112412f168.grb",
   "p168m_2026112500f168.grb",
   "p168m_2026112512f168.grb"
  ]
 },
 "nomads wpc qpf": {
  "status": 403,
  "sample": []
 },
 "wpc ero kml/shp": {
  "status": 200,
  "sample": [
   "EXCESSIVERAIN_Day2_latest.tar",
   "EXCESSIVERAIN_Day2_latest.zip",
   "EXCESSIVERAIN_Day2_newbins_latest.tar",
   "EXCESSIVERAIN_Day2_newbins_latest.zip",
   "EXCESSIVERAIN_Day2_newbins__latest.zip",
   "EXCESSIVERAIN_Day3_latest.tar",
   "EXCESSIVERAIN_Day3_latest.zip",
   "EXCESSIVERAIN_Day3_newbins_latest.tar",
   "EXCESSIVERAIN_Day3_newbins_latest.zip",
   "EXCESSIVERAIN_Day4_latest.tar",
   "EXCESSIVERAIN_Day4_latest.zip",
   "EXCESSIVERAIN_Day4_newbins_latest.zip",
   "EXCESSIVERAIN_Day5_latest.tar",
   "EXCESSIVERAIN_Day5_latest.zip",
   "EXCESSIVERAIN_Day5_newbins_latest.zip"
  ]
 },
 "wpc archive": {
  "status": 404,
  "sample": []
 }
}
```

## HREF

```
{
 "nomads days": {
  "status": 404,
  "days": []
 },
 "aws noaa-href-pds": {
  "status": 404,
  "prefixes": [],
  "keys": []
 }
}
```

## NBM (AWS)

```
{
 "status": 200,
 "prefixes": [
  "blend.20261125/"
 ],
 "keys": [
  "blend.20261125/00/core/blend.t00z.core.f001.ak.grib2",
  "blend.20261125/00/core/blend.t00z.core.f001.ak.grib2.idx",
  "blend.20261125/00/core/blend.t00z.core.f001.co.grib2"
 ]
}
```

## HRRR (AWS)

```
{
 "status": 200,
 "prefixes": [
  "hrrr.20261125/conus/"
 ],
 "keys": [
  "hrrr.20261125/conus/hrrr.t00z.bufrsnd.tar.gz",
  "hrrr.20261125/conus/hrrr.t00z.class1.bufr.tm00",
  "hrrr.20261125/conus/hrrr.t00z.wrfnatf00.grib2"
 ]
}
```

## NBM archive 30 d

```
{
 "status": 200,
 "prefixes": [
  "blend.20261026/"
 ],
 "keys": [
  "blend.20261026/00/core/blend.t00z.core.f001.ak.grib2",
  "blend.20261026/00/core/blend.t00z.core.f001.ak.grib2.idx",
  "blend.20261026/00/core/blend.t00z.core.f001.co.grib2"
 ]
}
```

## HREF AWS? (by date)

```
{
 "status": 404,
 "prefixes": [],
 "keys": []
}
```

## IEM AFOS (text products archive)

```
{
 "status": 200
}
```

