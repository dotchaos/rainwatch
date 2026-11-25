{
 "run": "20261125T212919Z",
 "sources": {
  "nws_gridpoint": {
   "status": "ok",
   "seconds": 0.1,
   "failures": 0
  },
  "wpc_ero": {
   "status": "ok",
   "seconds": 2.3,
   "failures": 0
  },
  "wpc_qpf": {
   "status": "ok",
   "seconds": 299.5,
   "failures": 0
  },
  "refs": {
   "status": "ok",
   "seconds": 1.8,
   "failures": 0
  }
 },
 "counts": {
  "nws_gridpoint": {
   "new": 2
  },
  "wpc_ero": {
   "new": 5
  },
  "wpc_qpf": {
   "new": 1646
  }
 },
 "failures": 0,
 "files_written": 7
}
# Collector live test

## Run log

```
{
 "run": "20261125T212919Z",
 "collector_version": "1.0",
 "started": "2026-11-25T21:29:19.534133+00:00",
 "sources": {
  "nws_gridpoint": {
   "status": "ok",
   "seconds": 0.1,
   "failures": 0
  },
  "wpc_ero": {
   "status": "ok",
   "seconds": 2.3,
   "failures": 0
  },
  "wpc_qpf": {
   "status": "ok",
   "seconds": 299.5,
   "failures": 0
  },
  "refs": {
   "status": "ok",
   "seconds": 1.8,
   "failures": 0
  }
 },
 "nws_update_time": "2026-11-25T20:26:28+00:00",
 "wpc_qpf_files_listed": 823,
 "refs_cycles_listed": [
  "2026112400",
  "2026112406",
  "2026112412",
  "2026112418",
  "2026112500",
  "2026112506",
  "2026112512",
  "2026112518"
 ],
 "refs_stopped_for_time": true,
 "finished": "2026-11-25T21:34:23.249549+00:00",
 "http_requests": 834,
 "counts": {
  "nws_gridpoint": {
   "new": 2
  },
  "wpc_ero": {
   "new": 5
  },
  "wpc_qpf": {
   "new": 1646
  }
 }
}
```

Failures (0):

```
[]
```

## nws_gridpoint: 2 records {'forecast': 2}

```
{
 "type": "forecast",
 "key": "nws|qpf|2026-11-25T20:26:28+00:00",
 "product": "qpf",
 "field": "quantitativePrecipitation",
 "issued": "2026-11-25T20:26:28+00:00",
 "valid_start": "2026-11-25T14:00:00+00:00",
 "valid_end": "2026-12-03T06:00:00+00:00",
 "interval_h": [
  4.0,
  6.0
 ],
 "units": "wmoUnit:mm",
 "periods": [
  {
   "valid_start": "2026-11-25T14:00:00+00:00",
   "valid_end": "2026-11-25T18:00:00+00:00",
   "interval_h": 4.0,
   "value": 0.254
  },
  {
   "valid_start": "2026-11-25T18:00:00+00:00",
   "valid_end": "2026-11-26T00:00:00+00:00",
   "interval_h": 6.0,
   "value": 0
  },
  {
   "valid_start": "2026-11-26T00:00:00+00:00",
   "valid_end": "2026-11-26T06:00:00+00:00",
   "interval_h": 6.0,
   "value": 0
  }
 ],
 "grid": [
  "MTR",
  "85,105"
 ],
 "url": "https://api.weather.gov/gridpoints/MTR/85,105",
 "sha256": "3deb03d68877231fa93250148d2e3433bce6248a938fcd2ad0a73c32b23109b1",
 "retrieved": "2026-11-25T21:29:19.662830+00:00",
 "source": "nws_gridpoint"
}
```

```
{
 "type": "forecast",
 "key": "nws|pop|2026-11-25T20:26:28+00:00",
 "product": "pop",
 "field": "probabilityOfPrecipitation",
 "issued": "2026-11-25T20:26:28+00:00",
 "valid_start": "2026-11-25T14:00:00+00:00",
 "valid_end": "2026-12-03T06:00:00+00:00",
 "interval_h": [
  1.0,
  6.0,
  12.0,
  18.0,
  48.0
 ],
 "units": "wmoUnit:percent",
 "periods": [
  {
   "valid_start": "2026-11-25T14:00:00+00:00",
   "valid_end": "2026-11-25T15:00:00+00:00",
   "interval_h": 1.0,
   "value": 12
  },
  {
   "valid_start": "2026-11-25T15:00:00+00:00",
   "valid_end": "2026-11-25T16:00:00+00:00",
   "interval_h": 1.0,
   "value": 5
  },
  {
   "valid_start": "2026-11-25T16:00:00+00:00",
   "valid_end": "2026-11-25T17:00:00+00:00",
   "interval_h": 1.0,
   "value": 3
  }
 ],
 "grid": [
  "MTR",
  "85,105"
 ],
 "url": "https://api.weather.gov/gridpoints/MTR/85,105",
 "sha256": "7cce0690c912b41b153449e0dc77cce65945134bdeb31ca90d5a4bff202350ef",
 "retrieved": "2026-11-25T21:29:19.662830+00:00",
 "source": "nws_gridpoint"
}
```

## wpc_ero: 5 records {'forecast': 5}

```
{
 "type": "forecast",
 "key": "ero|day1|2026-11-25 15:42:00",
 "product": "day1",
 "field": "ERO category",
 "issued": "2026-11-25 15:42:00",
 "valid_start": "16Z 11/25/26 - 12Z 11/26/26",
 "valid_end": "2026-11-26 12:00:00",
 "last_modified": "Wed, 25 Nov 2026 20:00:47 GMT",
 "url": "https://ftp.wpc.ncep.noaa.gov/shapefiles/qpf/excessive/EXCESSIVERAIN_Day1_latest.zip",
 "bytes": 7666,
 "sha256": "7f8fbdff916fcdcedbbba4429f516fef22fc0641a14774a06e066402e2919699",
 "retrieved": "2026-11-25T21:29:20.760947+00:00",
 "fields": [
  "dn",
  "PRODUCT",
  "VALID_TIME",
  "OUTLOOK",
  "ISSUE_TIME",
  "START_TIME",
  "END_TIME",
  "Snippet"
 ],
 "polygons": 6,
 "containing": [],
 "category": "none (outside all areas)",
 "category_rank": 0,
 "issue_attr": "2026-11-25 15:42:00",
 "start_attr": "16Z 11/25/26 - 12Z 11/26/26",
 "end_attr": "2026-11-26 12:00:00",
 "source": "wpc_ero"
}
```

```
{
 "type": "forecast",
 "key": "ero|day2|2026-11-25 19:49:00",
 "product": "day2",
 "field": "ERO category",
 "issued": "2026-11-25 19:49:00",
 "valid_start": "12Z 11/26/26 - 12Z 11/27/26",
 "valid_end": "2026-11-27 12:00:00",
 "last_modified": "Wed, 25 Nov 2026 20:00:53 GMT",
 "url": "https://ftp.wpc.ncep.noaa.gov/shapefiles/qpf/excessive/EXCESSIVERAIN_Day2_latest.zip",
 "bytes": 4837,
 "sha256": "de68c566b46755a536c6977c995687493dde0dcd60b5d56b0e336d7e75621355",
 "retrieved": "2026-11-25T21:29:21.118542+00:00",
 "fields": [
  "dn",
  "PRODUCT",
  "VALID_TIME",
  "OUTLOOK",
  "ISSUE_TIME",
  "START_TIME",
  "END_TIME",
  "Snippet"
 ],
 "polygons": 3,
 "containing": [],
 "category": "none (outside all areas)",
 "category_rank": 0,
 "issue_attr": "2026-11-25 19:49:00",
 "start_attr": "12Z 11/26/26 - 12Z 11/27/26",
 "end_attr": "2026-11-27 12:00:00",
 "source": "wpc_ero"
}
```

## wpc_qpf: 1646 records {'forecast': 823, 'file': 823}

```
{
 "type": "forecast",
 "key": "wpc_qpf|p06m|2026112000|f006",
 "product": "p06m",
 "field": "QPF",
 "issued": "2026-11-20T00:00:00+00:00",
 "fh": 6,
 "valid_start": "2026-11-20T00:00:00+00:00",
 "valid_end": "2026-11-20T06:00:00+00:00",
 "interval_h": 6,
 "url": "https://ftp.wpc.ncep.noaa.gov/2p5km_qpf/p06m_2026112000f006.grb",
 "listed_mtime": "19-Nov-2026 21:51",
 "last_modified": "Thu, 19 Nov 2026 21:51:45 GMT",
 "bytes": 154640,
 "sha256": "94ea8f4b92ccc23046a4bb5e17e6174e9b32fc4433661df5ac8c2fecbdf8cf67",
 "retrieved": "2026-11-25T21:29:22.872002+00:00",
 "wmo_header": "LEMB98 KWNH 200000",
 "block_cell": {
  "row": 766,
  "col": 121,
  "lat": 37.77233,
  "lon": -122.4095,
  "dist_km": 1.35,
  "value": 0.0
 },
 "cells": {
  "values(first row)": [
   0.0,
   0.0,
   0.0,
   0.0,
   0.0
  ]
 },
 "units": "kg m**-2",
 "source": "wpc_qpf"
}
```

```
{
 "type": "forecast",
 "key": "wpc_qpf|p06m|2026112000|f012",
 "product": "p06m",
 "field": "QPF",
 "issued": "2026-11-20T00:00:00+00:00",
 "fh": 12,
 "valid_start": "2026-11-20T06:00:00+00:00",
 "valid_end": "2026-11-20T12:00:00+00:00",
 "interval_h": 6,
 "url": "https://ftp.wpc.ncep.noaa.gov/2p5km_qpf/p06m_2026112000f012.grb",
 "listed_mtime": "19-Nov-2026 21:52",
 "last_modified": "Thu, 19 Nov 2026 21:52:54 GMT",
 "bytes": 147131,
 "sha256": "fa96e1c002021ddb77fc4e3aa2b65ceac4983d33cde08f6474561af97d75d7ac",
 "retrieved": "2026-11-25T21:29:23.910318+00:00",
 "wmo_header": "LEMC98 KWNH 200000",
 "block_cell": {
  "row": 766,
  "col": 121,
  "lat": 37.77233,
  "lon": -122.4095,
  "dist_km": 1.35,
  "value": 1.25
 },
 "cells": {
  "values(first row)": [
   2.375,
   2.75,
   2.125,
   1.5,
   1.5
  ]
 },
 "units": "kg m**-2",
 "source": "wpc_qpf"
}
```

