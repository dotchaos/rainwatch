{
 "run": "20261125T213552Z",
 "sources": {
  "nws_gridpoint": {
   "status": "ok",
   "seconds": 0.1,
   "failures": 0
  },
  "wpc_ero": {
   "status": "ok",
   "seconds": 0.5,
   "failures": 0
  },
  "refs": {
   "status": "ok",
   "seconds": 240.0,
   "failures": 0
  },
  "wpc_qpf": {
   "status": "ok",
   "seconds": 91.5,
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
   "new": 1135
  },
  "wpc_qpf": {
   "new": 1646
  }
 },
 "failures": 0,
 "files_written": 9
}
# Collector live test

## Run log

```
{
 "run": "20261125T213552Z",
 "collector_version": "1.0",
 "started": "2026-11-25T21:35:52.547345+00:00",
 "sources": {
  "nws_gridpoint": {
   "status": "ok",
   "seconds": 0.1,
   "failures": 0
  },
  "wpc_ero": {
   "status": "ok",
   "seconds": 0.5,
   "failures": 0
  },
  "refs": {
   "status": "ok",
   "seconds": 240.0,
   "failures": 0
  },
  "wpc_qpf": {
   "status": "ok",
   "seconds": 91.5,
   "failures": 0
  }
 },
 "nws_update_time": "2026-11-25T20:26:28+00:00",
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
 "wpc_qpf_files_listed": 823,
 "finished": "2026-11-25T21:41:24.715555+00:00",
 "http_requests": 1298,
 "counts": {
  "nws_gridpoint": {
   "new": 2
  },
  "wpc_ero": {
   "new": 5
  },
  "refs": {
   "new": 1135
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
 "retrieved": "2026-11-25T21:35:52.621860+00:00",
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
 "retrieved": "2026-11-25T21:35:52.621860+00:00",
 "source": "nws_gridpoint"
}
```

## refs: 1135 records {'forecast': 906, 'file': 229}

```
{
 "type": "forecast",
 "key": "refs|avrg|2026112518|APCP:surface:0-1 hour acc fcst:wt ens mean:process=193",
 "product": "avrg",
 "field": "APCP",
 "descriptor": "APCP:surface:0-1 hour acc fcst:wt ens mean:process=193",
 "issued": "2026-11-25T18:00:00+00:00",
 "fh": 1,
 "valid_start": "2026-11-25T18:00:00+00:00",
 "valid_end": "2026-11-25T19:00:00+00:00",
 "interval_h": 1,
 "threshold": null,
 "members": "14",
 "url": "https://nomads.ncep.noaa.gov/pub/data/nccf/com/refs/prod/refs.20261125/18/ensprod/refs.t18z.avrg.f01.conus.grib2",
 "byte_range": "0-",
 "sha256": "6cd42e01e944ae68c60d4b1c65140f4c9b3e783209d8e1f89d45e59601dfd9a7",
 "retrieved": "2026-11-25T21:35:55.805402+00:00",
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
 "key": "refs|eas|2026112518|APCP:surface:0-1 hour acc fcst:prob >0.254:prob fcst 0/14:process=197",
 "product": "eas",
 "field": "APCP",
 "descriptor": "APCP:surface:0-1 hour acc fcst:prob >0.254:prob fcst 0/14:process=197",
 "issued": "2026-11-25T18:00:00+00:00",
 "fh": 1,
 "valid_start": "2026-11-25T18:00:00+00:00",
 "valid_end": "2026-11-25T19:00:00+00:00",
 "interval_h": 1,
 "threshold": {
  "op": ">",
  "value": 0.254,
  "text": "prob >0.254"
 },
 "members": null,
 "url": "https://nomads.ncep.noaa.gov/pub/data/nccf/com/refs/prod/refs.20261125/18/ensprod/refs.t18z.eas.f01.conus.grib2",
 "byte_range": "0-320274",
 "sha256": "fbb85abf0d4f15ae1831757a047edae5e3c1317323fe1dcdc9ab3bcb7c92e20c",
 "retrieved": "2026-11-25T21:35:56.818836+00:00",
 "block_cell": {
  "row": 600,
  "col": 178,
  "lat": 37.76331,
  "lon": -122.41286,
  "dist_km": 0.32,
  "value": 0.03125
 },
 "cells": {
  "values(first row)": [
   0.03125,
   0.03125,
   0.03125,
   0.03125,
   0.03125
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
 "key": "ero|day1|2026-11-25 15:42:00",
 "product": "day1",
 "field": "ERO category",
 "issued": "2026-11-25 15:42:00",
 "valid_start": "2026-11-25 16:00:00",
 "valid_end": "2026-11-26 12:00:00",
 "last_modified": "Wed, 25 Nov 2026 20:00:47 GMT",
 "url": "https://ftp.wpc.ncep.noaa.gov/shapefiles/qpf/excessive/EXCESSIVERAIN_Day1_latest.zip",
 "bytes": 7666,
 "sha256": "7f8fbdff916fcdcedbbba4429f516fef22fc0641a14774a06e066402e2919699",
 "retrieved": "2026-11-25T21:35:53.023327+00:00",
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
 "start_attr": "2026-11-25 16:00:00",
 "end_attr": "2026-11-26 12:00:00",
 "valid_text": "16Z 11/25/26 - 12Z 11/26/26",
 "time_zone_note": "WPC attribute times are recorded exactly as published (no zone given in the file)",
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
 "valid_start": "2026-11-26 12:00:00",
 "valid_end": "2026-11-27 12:00:00",
 "last_modified": "Wed, 25 Nov 2026 20:00:53 GMT",
 "url": "https://ftp.wpc.ncep.noaa.gov/shapefiles/qpf/excessive/EXCESSIVERAIN_Day2_latest.zip",
 "bytes": 4837,
 "sha256": "de68c566b46755a536c6977c995687493dde0dcd60b5d56b0e336d7e75621355",
 "retrieved": "2026-11-25T21:35:53.072731+00:00",
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
 "start_attr": "2026-11-26 12:00:00",
 "end_attr": "2026-11-27 12:00:00",
 "valid_text": "12Z 11/26/26 - 12Z 11/27/26",
 "time_zone_note": "WPC attribute times are recorded exactly as published (no zone given in the file)",
 "source": "wpc_ero"
}
```

## wpc_qpf: 1646 records {'forecast': 823, 'file': 823}

```
{
 "type": "forecast",
 "key": "wpc_qpf|p06m|2026112600|f168",
 "product": "p06m",
 "field": "QPF",
 "issued": "2026-11-26T00:00:00+00:00",
 "fh": 168,
 "valid_start": "2026-12-02T18:00:00+00:00",
 "valid_end": "2026-12-03T00:00:00+00:00",
 "interval_h": 6,
 "url": "https://ftp.wpc.ncep.noaa.gov/2p5km_qpf/p06m_2026112600f168.grb",
 "listed_mtime": "25-Nov-2026 20:46",
 "last_modified": "Wed, 25 Nov 2026 20:46:33 GMT",
 "bytes": 56003,
 "sha256": "ee5659d679ed9dc47786844c9b708f08a45824e0e8e9114f601e10607d1c1cf6",
 "retrieved": "2026-11-25T21:39:53.315052+00:00",
 "wmo_header": "LEMQ98 KWNH 260000",
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
 "key": "wpc_qpf|p24m|2026112600|f168",
 "product": "p24m",
 "field": "QPF",
 "issued": "2026-11-26T00:00:00+00:00",
 "fh": 168,
 "valid_start": "2026-12-02T00:00:00+00:00",
 "valid_end": "2026-12-03T00:00:00+00:00",
 "interval_h": 24,
 "url": "https://ftp.wpc.ncep.noaa.gov/2p5km_qpf/p24m_2026112600f168.grb",
 "listed_mtime": "25-Nov-2026 16:40",
 "last_modified": "Wed, 25 Nov 2026 16:40:42 GMT",
 "bytes": 125678,
 "sha256": "5eb0a47678d6900076b96fac0657ef5bb23ea24e0c416e35164c3a154198d3b6",
 "retrieved": "2026-11-25T21:39:53.676248+00:00",
 "wmo_header": null,
 "block_cell": {
  "row": 766,
  "col": 121,
  "lat": 37.77233,
  "lon": -122.4095,
  "dist_km": 1.35,
  "value": 5.75
 },
 "cells": {
  "values(first row)": [
   6.125,
   5.875,
   5.875,
   5.875,
   5.75
  ]
 },
 "units": "kg m**-2",
 "source": "wpc_qpf"
}
```

