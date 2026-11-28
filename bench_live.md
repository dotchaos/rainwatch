{
 "run": "20261128T144639Z",
 "sources": {
  "nws_gridpoint": {
   "status": "ok",
   "seconds": 0.1,
   "failures": 0
  },
  "wpc_ero": {
   "status": "ok",
   "seconds": 1.2,
   "failures": 0
  },
  "refs": {
   "status": "ok",
   "seconds": 239.5,
   "failures": 0
  },
  "wpc_qpf": {
   "status": "ok",
   "seconds": 119.3,
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
  "refs": {
   "new": 1050
  },
  "wpc_qpf": {
   "new": 1594
  }
 },
 "failures": 0,
 "files_written": 9
}
# Collector live test

## Run log

```
{
 "run": "20261128T144639Z",
 "collector_version": "1.0",
 "started": "2026-11-28T14:46:39.213906+00:00",
 "sources": {
  "nws_gridpoint": {
   "status": "ok",
   "seconds": 0.1,
   "failures": 0
  },
  "wpc_ero": {
   "status": "ok",
   "seconds": 1.2,
   "failures": 0
  },
  "refs": {
   "status": "ok",
   "seconds": 239.5,
   "failures": 0
  },
  "wpc_qpf": {
   "status": "ok",
   "seconds": 119.3,
   "failures": 0
  }
 },
 "nws_update_time": "2026-11-28T12:25:26+00:00",
 "refs_cycles_listed": [
  "2026112700",
  "2026112706",
  "2026112712",
  "2026112718",
  "2026112800",
  "2026112806",
  "2026112812"
 ],
 "refs_stopped_for_time": true,
 "wpc_qpf_stopped_for_time": true,
 "wpc_qpf_files_listed": 831,
 "finished": "2026-11-28T14:52:39.268442+00:00",
 "http_requests": 1283,
 "counts": {
  "nws_gridpoint": {
   "new": 2
  },
  "wpc_ero": {
   "new": 5
  },
  "refs": {
   "new": 1050
  },
  "wpc_qpf": {
   "new": 1594
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
 "key": "nws|qpf|2026-11-28T12:25:26+00:00",
 "product": "qpf",
 "field": "quantitativePrecipitation",
 "issued": "2026-11-28T12:25:26+00:00",
 "valid_start": "2026-11-28T06:00:00+00:00",
 "valid_end": "2026-12-06T06:00:00+00:00",
 "interval_h": [
  6.0
 ],
 "units": "wmoUnit:mm",
 "periods": [
  {
   "valid_start": "2026-11-28T06:00:00+00:00",
   "valid_end": "2026-11-28T12:00:00+00:00",
   "interval_h": 6.0,
   "value": 0
  },
  {
   "valid_start": "2026-11-28T12:00:00+00:00",
   "valid_end": "2026-11-28T18:00:00+00:00",
   "interval_h": 6.0,
   "value": 0
  },
  {
   "valid_start": "2026-11-28T18:00:00+00:00",
   "valid_end": "2026-11-29T00:00:00+00:00",
   "interval_h": 6.0,
   "value": 0
  }
 ],
 "grid": [
  "MTR",
  "85,105"
 ],
 "url": "https://api.weather.gov/gridpoints/MTR/85,105",
 "sha256": "d6875001f1cfd61c0512fa7cd448313189cfe5690781163440dcef6f0111dc87",
 "retrieved": "2026-11-28T14:46:39.294735+00:00",
 "source": "nws_gridpoint"
}
```

```
{
 "type": "forecast",
 "key": "nws|pop|2026-11-28T12:25:26+00:00",
 "product": "pop",
 "field": "probabilityOfPrecipitation",
 "issued": "2026-11-28T12:25:26+00:00",
 "valid_start": "2026-11-28T06:00:00+00:00",
 "valid_end": "2026-12-06T06:00:00+00:00",
 "interval_h": [
  1.0,
  3.0,
  6.0,
  12.0,
  18.0,
  30.0
 ],
 "units": "wmoUnit:percent",
 "periods": [
  {
   "valid_start": "2026-11-28T06:00:00+00:00",
   "valid_end": "2026-11-28T09:00:00+00:00",
   "interval_h": 3.0,
   "value": 0
  },
  {
   "valid_start": "2026-11-28T09:00:00+00:00",
   "valid_end": "2026-11-28T12:00:00+00:00",
   "interval_h": 3.0,
   "value": 1
  },
  {
   "valid_start": "2026-11-28T12:00:00+00:00",
   "valid_end": "2026-11-29T06:00:00+00:00",
   "interval_h": 18.0,
   "value": 0
  }
 ],
 "grid": [
  "MTR",
  "85,105"
 ],
 "url": "https://api.weather.gov/gridpoints/MTR/85,105",
 "sha256": "c6fec4dd2ab17f0fe138a1fdd15582587ac58b59fe7d1f197d612951ca364af6",
 "retrieved": "2026-11-28T14:46:39.294735+00:00",
 "source": "nws_gridpoint"
}
```

## refs: 1050 records {'forecast': 809, 'file': 241}

```
{
 "type": "forecast",
 "key": "refs|avrg|2026112812|APCP:surface:0-1 hour acc fcst:wt ens mean:process=193",
 "product": "avrg",
 "field": "APCP",
 "descriptor": "APCP:surface:0-1 hour acc fcst:wt ens mean:process=193",
 "issued": "2026-11-28T12:00:00+00:00",
 "fh": 1,
 "valid_start": "2026-11-28T12:00:00+00:00",
 "valid_end": "2026-11-28T13:00:00+00:00",
 "interval_h": 1,
 "threshold": null,
 "members": "14",
 "url": "https://nomads.ncep.noaa.gov/pub/data/nccf/com/refs/prod/refs.20261128/12/ensprod/refs.t12z.avrg.f01.conus.grib2",
 "byte_range": "0-",
 "sha256": "acd56f8b907f346782d3e670dc944f0776cdc41b4cae2f71b7c6923e0b500edc",
 "retrieved": "2026-11-28T14:46:43.090592+00:00",
 "block_cell": {
  "row": 600,
  "col": 178,
  "lat": 37.76344,
  "lon": -122.41227,
  "dist_km": 0.36,
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
 "source": "refs"
}
```

```
{
 "type": "forecast",
 "key": "refs|eas|2026112812|APCP:surface:0-1 hour acc fcst:prob >0.254:prob fcst 0/14:process=197",
 "product": "eas",
 "field": "APCP",
 "descriptor": "APCP:surface:0-1 hour acc fcst:prob >0.254:prob fcst 0/14:process=197",
 "issued": "2026-11-28T12:00:00+00:00",
 "fh": 1,
 "valid_start": "2026-11-28T12:00:00+00:00",
 "valid_end": "2026-11-28T13:00:00+00:00",
 "interval_h": 1,
 "threshold": {
  "op": ">",
  "value": 0.254,
  "text": "prob >0.254"
 },
 "members": null,
 "url": "https://nomads.ncep.noaa.gov/pub/data/nccf/com/refs/prod/refs.20261128/12/ensprod/refs.t12z.eas.f01.conus.grib2",
 "byte_range": "0-283227",
 "sha256": "1715800b7e3996b55c7c4eb35bb063a08e664e29a9b62d3e8663b1518d6ce2fc",
 "retrieved": "2026-11-28T14:46:44.201658+00:00",
 "block_cell": {
  "row": 600,
  "col": 178,
  "lat": 37.76331,
  "lon": -122.41286,
  "dist_km": 0.32,
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
 "source": "refs"
}
```

## wpc_ero: 5 records {'forecast': 5}

```
{
 "type": "forecast",
 "key": "ero|day1|2026-11-28 08:00:00",
 "product": "day1",
 "field": "ERO category",
 "issued": "2026-11-28 08:00:00",
 "valid_start": "2026-11-28 12:00:00",
 "valid_end": "2026-11-29 12:00:00",
 "last_modified": "Sat, 28 Nov 2026 08:30:37 GMT",
 "url": "https://ftp.wpc.ncep.noaa.gov/shapefiles/qpf/excessive/EXCESSIVERAIN_Day1_latest.zip",
 "bytes": 1686,
 "sha256": "19ad7e31d5b43b137b398eccc39616b5f5773b59ce406ee909fc29d5b355d2f9",
 "retrieved": "2026-11-28T14:46:39.980456+00:00",
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
 "polygons": 1,
 "containing": [],
 "category": "none (outside all areas)",
 "category_rank": 0,
 "issue_attr": "2026-11-28 08:00:00",
 "start_attr": "2026-11-28 12:00:00",
 "end_attr": "2026-11-29 12:00:00",
 "valid_text": "12Z 11/28/26 - 12Z 11/29/26",
 "time_zone_note": "WPC attribute times are recorded exactly as published (no zone given in the file)",
 "source": "wpc_ero"
}
```

```
{
 "type": "forecast",
 "key": "ero|day2|2026-11-28 08:00:00",
 "product": "day2",
 "field": "ERO category",
 "issued": "2026-11-28 08:00:00",
 "valid_start": "2026-11-29 12:00:00",
 "valid_end": "2026-11-30 12:00:00",
 "last_modified": "Sat, 28 Nov 2026 08:15:42 GMT",
 "url": "https://ftp.wpc.ncep.noaa.gov/shapefiles/qpf/excessive/EXCESSIVERAIN_Day2_latest.zip",
 "bytes": 2011,
 "sha256": "1f1b68b946e0e75bca0274d78520ddab78c71922db3f4d5009ffb8d46c17d274",
 "retrieved": "2026-11-28T14:46:40.180657+00:00",
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
 "polygons": 1,
 "containing": [],
 "category": "none (outside all areas)",
 "category_rank": 0,
 "issue_attr": "2026-11-28 08:00:00",
 "start_attr": "2026-11-29 12:00:00",
 "end_attr": "2026-11-30 12:00:00",
 "valid_text": "12Z 11/29/26 - 12Z 11/30/26",
 "time_zone_note": "WPC attribute times are recorded exactly as published (no zone given in the file)",
 "source": "wpc_ero"
}
```

## wpc_qpf: 1594 records {'forecast': 797, 'file': 797}

```
{
 "type": "forecast",
 "key": "wpc_qpf|p06m|2026112812|f168",
 "product": "p06m",
 "field": "QPF",
 "issued": "2026-11-28T12:00:00+00:00",
 "fh": 168,
 "valid_start": "2026-12-05T06:00:00+00:00",
 "valid_end": "2026-12-05T12:00:00+00:00",
 "interval_h": 6,
 "url": "https://ftp.wpc.ncep.noaa.gov/2p5km_qpf/p06m_2026112812f168.grb",
 "listed_mtime": "28-Nov-2026 08:46",
 "last_modified": "Sat, 28 Nov 2026 08:46:41 GMT",
 "bytes": 97674,
 "sha256": "909cfa88f987178361ce17ed4cb42bf884e0b73048fd1119d06c4c024494cd4e",
 "retrieved": "2026-11-28T14:50:40.475301+00:00",
 "wmo_header": "LEMQ98 KWNH 281200",
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
 "key": "wpc_qpf|p24m|2026112812|f168",
 "product": "p24m",
 "field": "QPF",
 "issued": "2026-11-28T12:00:00+00:00",
 "fh": 168,
 "valid_start": "2026-12-04T12:00:00+00:00",
 "valid_end": "2026-12-05T12:00:00+00:00",
 "interval_h": 24,
 "url": "https://ftp.wpc.ncep.noaa.gov/2p5km_qpf/p24m_2026112812f168.grb",
 "listed_mtime": "28-Nov-2026 04:47",
 "last_modified": "Sat, 28 Nov 2026 04:47:50 GMT",
 "bytes": 163612,
 "sha256": "d2fd99d4098307c96a1486e0e39a2ef7a86ed57796512f6eceabf216c6e51ad1",
 "retrieved": "2026-11-28T14:50:41.083282+00:00",
 "wmo_header": null,
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
   0.25,
   0.25,
   0.25,
   0.25,
   0.25
  ]
 },
 "units": "kg m**-2",
 "source": "wpc_qpf"
}
```

