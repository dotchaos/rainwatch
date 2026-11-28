{
 "run": "20261128T173309Z",
 "execution_ok": true,
 "collection_complete": false,
 "sources": {
  "nws_gridpoint": {
   "execution": "ok",
   "collection": "complete",
   "incomplete_reason": null,
   "seconds": 0.0,
   "failures": 0
  },
  "wpc_ero": {
   "execution": "ok",
   "collection": "complete",
   "incomplete_reason": null,
   "seconds": 0.7,
   "failures": 0
  },
  "refs": {
   "execution": "ok with request failures",
   "collection": "incomplete",
   "incomplete_reason": "time limit",
   "seconds": 239.4,
   "failures": 27
  },
  "wpc_qpf": {
   "execution": "ok",
   "collection": "complete",
   "incomplete_reason": null,
   "seconds": 86.1,
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
   "new": 3771
  },
  "wpc_qpf": {
   "new": 1615
  }
 },
 "failures": 27,
 "files_written": 9
}
# Collector live test

## Run log

```
{
 "run": "20261128T173309Z",
 "collector_version": "1.1",
 "started": "2026-11-28T17:33:09.039350+00:00",
 "sources": {
  "nws_gridpoint": {
   "execution": "ok",
   "collection": "complete",
   "incomplete_reason": null,
   "seconds": 0.0,
   "failures": 0
  },
  "wpc_ero": {
   "execution": "ok",
   "collection": "complete",
   "incomplete_reason": null,
   "seconds": 0.7,
   "failures": 0
  },
  "refs": {
   "execution": "ok with request failures",
   "collection": "incomplete",
   "incomplete_reason": "time limit",
   "seconds": 239.4,
   "failures": 27
  },
  "wpc_qpf": {
   "execution": "ok",
   "collection": "complete",
   "incomplete_reason": null,
   "seconds": 86.1,
   "failures": 0
  }
 },
 "coverage": {
  "nws_gridpoint": {
   "complete": true,
   "empty_products": []
  },
  "wpc_ero": {
   "days_ok": 5,
   "days_failed": 0,
   "unknown": 0,
   "complete": true
  },
  "refs": {
   "listed_on_server": 2940,
   "collected": 201,
   "outstanding": 2739,
   "collected_this_run": 201,
   "revised_this_run": 0,
   "deferred_this_run": 2712,
   "oldest_outstanding_cycle": "2026-11-27T00:00:00+00:00",
   "awaiting_publication": 0,
   "awaiting_sample": [],
   "expired_declared": 0,
   "complete": false,
   "reason": "time limit"
  },
  "wpc_qpf": {
   "listed_on_server": 807,
   "collected": 807,
   "outstanding": 0,
   "collected_this_run": 807,
   "revised_this_run": 0,
   "deferred_this_run": 0,
   "awaiting_publication": 0,
   "expired_declared": 0,
   "complete": true,
   "reason": null
  }
 },
 "nws_update_time": "2026-11-28T12:25:26+00:00",
 "finished": "2026-11-28T17:38:35.147223+00:00",
 "http_requests": 1285,
 "requests_skipped_at_deadline": 1,
 "execution_ok": true,
 "collection_complete": false,
 "counts": {
  "nws_gridpoint": {
   "new": 2
  },
  "wpc_ero": {
   "new": 5
  },
  "refs": {
   "new": 3771
  },
  "wpc_qpf": {
   "new": 1615
  }
 }
}
```

Failures (27):

```
[
 {
  "source": "refs",
  "url": "https://nomads.ncep.noaa.gov/pub/data/nccf/com/refs/prod/refs.20261127/00/ensprod/refs.t00z.ffri.f01.conus.grib2",
  "error": "no precipitation (APCP) messages in the file's inventory",
  "idx_records": 1
 },
 {
  "source": "refs",
  "url": "https://nomads.ncep.noaa.gov/pub/data/nccf/com/refs/prod/refs.20261127/00/ensprod/refs.t00z.ffri.f02.conus.grib2",
  "error": "no precipitation (APCP) messages in the file's inventory",
  "idx_records": 1
 },
 {
  "source": "refs",
  "url": "https://nomads.ncep.noaa.gov/pub/data/nccf/com/refs/prod/refs.20261127/00/ensprod/refs.t00z.ffri.f03.conus.grib2",
  "error": "no precipitation (APCP) messages in the file's inventory",
  "idx_records": 2
 },
 {
  "source": "refs",
  "url": "https://nomads.ncep.noaa.gov/pub/data/nccf/com/refs/prod/refs.20261127/00/ensprod/refs.t00z.ffri.f04.conus.grib2",
  "error": "no precipitation (APCP) messages in the file's inventory",
  "idx_records": 1
 },
 {
  "source": "refs",
  "url": "https://nomads.ncep.noaa.gov/pub/data/nccf/com/refs/prod/refs.20261127/00/ensprod/refs.t00z.ffri.f05.conus.grib2",
  "error": "no precipitation (APCP) messages in the file's inventory",
  "idx_records": 1
 },
 {
  "source": "refs",
  "url": "https://nomads.ncep.noaa.gov/pub/data/nccf/com/refs/prod/refs.20261127/00/ensprod/refs.t00z.ffri.f07.conus.grib2",
  "error": "no precipitation (APCP) messages in the file's inventory",
  "idx_records": 1
 },
 {
  "source": "refs",
  "url": "https://nomads.ncep.noaa.gov/pub/data/nccf/com/refs/prod/refs.20261127/00/ensprod/refs.t00z.ffri.f08.conus.grib2",
  "error": "no precipitation (APCP) messages in the file's inventory",
  "idx_records": 1
 },
 {
  "source": "refs",
  "url": "https://nomads.ncep.noaa.gov/pub/data/nccf/com/refs/prod/refs.20261127/00/ensprod/refs.t00z.ffri.f10.conus.grib2",
  "error": "no precipitation (APCP) messages in the file's inventory",
  "idx_records": 1
 },
 {
  "source": "refs",
  "url": "https://nomads.ncep.noaa.gov/pub/data/nccf/com/refs/prod/refs.20261127/00/ensprod/refs.t00z.ffri.f11.conus.grib2",
  "error": "no precipitation (APCP) messages in the file's inventory",
  "idx_records": 1
 },
 {
  "source": "refs",
  "url": "https://nomads.ncep.noaa.gov/pub/data/nccf/com/refs/prod/refs.20261127/00/ensprod/refs.t00z.ffri.f13.conus.grib2",
  "error": "no precipitation (APCP) messages in the file's inventory",
  "idx_records": 1
 },
 {
  "source": "refs",
  "url": "https://nomads.ncep.noaa.gov/pub/data/nccf/com/refs/prod/refs.20261127/00/ensprod/refs.t00z.ffri.f14.conus.grib2",
  "error": "no precipitation (APCP) messages in the file's inventory",
  "idx_records": 1
 },
 {
  "source": "refs",
  "url": "https://nomads.ncep.noaa.gov/pub/data/nccf/com/refs/prod/refs.20261127/00/ensprod/refs.t00z.ffri.f16.conus.grib2",
  "error": "no precipitation (APCP) messages in the file's inventory",
  "idx_records": 1
 },
 {
  "source": "refs",
  "url": "https://nomads.ncep.noaa.gov/pub/data/nccf/com/refs/prod/refs.20261127/00/ensprod/refs.t00z.ffri.f17.conus.grib2",
  "error": "no precipitation (APCP) messages in the file's inventory",
  "idx_records": 1
 },
 {
  "source": "refs",
  "url": "https://nomads.ncep.noaa.gov/pub/data/nccf/com/refs/prod/refs.20261127/00/ensprod/refs.t00z.ffri.f19.conus.grib2",
  "error": "no precipitation (APCP) messages in the file's inventory",
  "idx_records": 1
 },
 {
  "source": "refs",
  "url": "https://nomads.ncep.noaa.gov/pub/data/nccf/com/refs/prod/refs.20261127/00/ensprod/refs.t00z.ffri.f20.conus.grib2",
  "error": "no precipitation (APCP) messages in the file's inventory",
  "idx_records": 1
 }
]
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
 "retrieved": "2026-11-28T17:33:09.069035+00:00",
 "empty_periods": false,
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
 "retrieved": "2026-11-28T17:33:09.069035+00:00",
 "empty_periods": false,
 "source": "nws_gridpoint"
}
```

## refs: 3771 records {'forecast': 831, 'file': 201, 'failed': 27, 'deferred': 2712}

```
{
 "type": "forecast",
 "key": "refs|avrg|2026112700|APCP:surface:0-1 hour acc fcst:wt ens mean:process=193",
 "product": "avrg",
 "field": "APCP",
 "descriptor": "APCP:surface:0-1 hour acc fcst:wt ens mean:process=193",
 "issued": "2026-11-27T00:00:00+00:00",
 "fh": 1,
 "valid_start": "2026-11-27T00:00:00+00:00",
 "valid_end": "2026-11-27T01:00:00+00:00",
 "interval_h": 1,
 "threshold": null,
 "members": "14",
 "url": "https://nomads.ncep.noaa.gov/pub/data/nccf/com/refs/prod/refs.20261127/00/ensprod/refs.t00z.avrg.f01.conus.grib2",
 "byte_range": "0-",
 "sha256": "d9ffb8228e9845999fc80404b49727fc9b4206f4f1638459da0108da77b0443e",
 "retrieved": "2026-11-28T17:33:15.535418+00:00",
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
 "key": "refs|eas|2026112700|APCP:surface:0-1 hour acc fcst:prob >0.254:prob fcst 0/14:process=197",
 "product": "eas",
 "field": "APCP",
 "descriptor": "APCP:surface:0-1 hour acc fcst:prob >0.254:prob fcst 0/14:process=197",
 "issued": "2026-11-27T00:00:00+00:00",
 "fh": 1,
 "valid_start": "2026-11-27T00:00:00+00:00",
 "valid_end": "2026-11-27T01:00:00+00:00",
 "interval_h": 1,
 "threshold": {
  "op": ">",
  "value": 0.254,
  "text": "prob >0.254"
 },
 "members": null,
 "url": "https://nomads.ncep.noaa.gov/pub/data/nccf/com/refs/prod/refs.20261127/00/ensprod/refs.t00z.eas.f01.conus.grib2",
 "byte_range": "0-363815",
 "sha256": "cf74be8b4eba57d51e2e011ef37128ba84a64a8e34b8e882f94da1e3f09daba9",
 "retrieved": "2026-11-28T17:33:16.460246+00:00",
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
 "key": "ero|day1|2026-11-28T15:27:00+00:00",
 "product": "day1",
 "field": "ERO category",
 "issued": "2026-11-28T15:27:00+00:00",
 "valid_start": "2026-11-28T16:00:00+00:00",
 "valid_end": "2026-11-29T12:00:00+00:00",
 "last_modified": "Sat, 28 Nov 2026 15:35:21 GMT",
 "url": "https://ftp.wpc.ncep.noaa.gov/shapefiles/qpf/excessive/EXCESSIVERAIN_Day1_latest.zip",
 "bytes": 1686,
 "sha256": "eeed520e056d18905af90b97e068ce29ecb6f7eee9a08a669c5bbd8626c1e74c",
 "retrieved": "2026-11-28T17:33:09.542039+00:00",
 "category": "none at the block",
 "category_rank": 0,
 "problems": [],
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
 "records": 1,
 "containing_ranks": [],
 "attributes": [
  {
   "dn": "0",
   "PRODUCT": "Day 1 Excessive Rainfall Potential Forecast",
   "VALID_TIME": "16Z 11/28/26 - 12Z 11/29/26",
   "OUTLOOK": "None Expected",
   "ISSUE_TIME": "2026-11-28 15:27:00",
   "START_TIME": "2026-11-28 16:00:00",
   "END_TIME": "2026-11-29 12:00:00",
   "Snippet": "16Z 11/28/26 - 12Z 11/29/26"
  }
 ],
 "prj": "GEOGCS[\"GCS_North_American_1983\",DATUM[\"D_North_American_1983\",SPHEROID[\"GRS_1980\",6378137.0,298.257222101]],PRIMEM[\"Greenwich\",0.0],UNIT[\"Degree\",0.0174532925199433]]",
 "source": "wpc_ero"
}
```

```
{
 "type": "forecast",
 "key": "ero|day2|2026-11-28T08:00:00+00:00",
 "product": "day2",
 "field": "ERO category",
 "issued": "2026-11-28T08:00:00+00:00",
 "valid_start": "2026-11-29T12:00:00+00:00",
 "valid_end": "2026-11-30T12:00:00+00:00",
 "last_modified": "Sat, 28 Nov 2026 08:15:42 GMT",
 "url": "https://ftp.wpc.ncep.noaa.gov/shapefiles/qpf/excessive/EXCESSIVERAIN_Day2_latest.zip",
 "bytes": 2011,
 "sha256": "1f1b68b946e0e75bca0274d78520ddab78c71922db3f4d5009ffb8d46c17d274",
 "retrieved": "2026-11-28T17:33:09.631617+00:00",
 "category": "none at the block",
 "category_rank": 0,
 "problems": [],
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
 "records": 1,
 "containing_ranks": [],
 "attributes": [
  {
   "dn": "1",
   "PRODUCT": "Day 2 Excessive Rainfall Potential Forecast",
   "VALID_TIME": "12Z 11/29/26 - 12Z 11/30/26",
   "OUTLOOK": "Marginal (At Least 5%)",
   "ISSUE_TIME": "2026-11-28 08:00:00",
   "START_TIME": "2026-11-29 12:00:00",
   "END_TIME": "2026-11-30 12:00:00",
   "Snippet": "12Z 11/29/26 - 12Z 11/30/26"
  }
 ],
 "prj": "GEOGCS[\"GCS_Sphere_EMEP\",DATUM[\"D_Sphere_EMEP\",SPHEROID[\"Sphere_EMEP\",6371200.0,0.0]],PRIMEM[\"Greenwich\",0.0],UNIT[\"Degree\",0.0174532925199433]]",
 "source": "wpc_ero"
}
```

## wpc_qpf: 1615 records {'unpublished': 1, 'forecast': 807, 'file': 807}

```
{
 "type": "forecast",
 "key": "wpc_qpf|p48m|2026111512|f120",
 "product": "p48m",
 "field": "QPF",
 "issued": "2026-11-15T12:00:00+00:00",
 "fh": 120,
 "valid_start": "2026-11-18T12:00:00+00:00",
 "valid_end": "2026-11-20T12:00:00+00:00",
 "interval_h": 48,
 "url": "https://ftp.wpc.ncep.noaa.gov/2p5km_qpf/p48m_2026111512f120.grb",
 "listing": "15-Nov-2026 05:09|215K",
 "last_modified": "Sun, 15 Nov 2026 05:09:55 GMT",
 "bytes": 220462,
 "sha256": "9e2d0057304aa0fe0f6b0e759b5324653e65bfd4a6d8eab134557f6b752ca5af",
 "retrieved": "2026-11-28T17:37:09.254696+00:00",
 "wmo_header": "LEMO98 KWNH 151200",
 "block_cell": {
  "row": 766,
  "col": 121,
  "lat": 37.77233,
  "lon": -122.4095,
  "dist_km": 1.35,
  "value": 60.375
 },
 "cells": {
  "values(first row)": [
   62.75,
   61.25,
   60.5,
   59.625,
   58.875
  ]
 },
 "units": "kg m**-2",
 "source": "wpc_qpf"
}
```

```
{
 "type": "forecast",
 "key": "wpc_qpf|p48m|2026111512|f168",
 "product": "p48m",
 "field": "QPF",
 "issued": "2026-11-15T12:00:00+00:00",
 "fh": 168,
 "valid_start": "2026-11-20T12:00:00+00:00",
 "valid_end": "2026-11-22T12:00:00+00:00",
 "interval_h": 48,
 "url": "https://ftp.wpc.ncep.noaa.gov/2p5km_qpf/p48m_2026111512f168.grb",
 "listing": "15-Nov-2026 05:28|224K",
 "last_modified": "Sun, 15 Nov 2026 05:28:11 GMT",
 "bytes": 229861,
 "sha256": "5815a2713dd11bdc57da3dd2e94eb4438b203493664a50c52b74f5eaec08d8ec",
 "retrieved": "2026-11-28T17:37:09.650625+00:00",
 "wmo_header": "LEMR98 KWNH 151200",
 "block_cell": {
  "row": 766,
  "col": 121,
  "lat": 37.77233,
  "lon": -122.4095,
  "dist_km": 1.35,
  "value": 0.75
 },
 "cells": {
  "values(first row)": [
   0.75,
   0.75,
   0.75,
   0.75,
   0.75
  ]
 },
 "units": "kg m**-2",
 "source": "wpc_qpf"
}
```

