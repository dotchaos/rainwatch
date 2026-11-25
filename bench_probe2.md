# External benchmarking: second access probe

Run at 2026-11-25 16:51 UTC from GitHub Actions.

## HREF

```
{
 "https://nomads.ncep.noaa.gov/pub/data/nccf/com/href/": {
  "url": "https://nomads.ncep.noaa.gov/pub/data/nccf/com/href/",
  "status": 404,
  "n": 0,
  "entries": []
 },
 "https://ftp.ncep.noaa.gov/data/nccf/com/href/": {
  "url": "https://ftp.ncep.noaa.gov/data/nccf/com/href/",
  "status": "error ConnectTimeout: HTTPSConnectionPool(host='ftp.ncep.noaa.gov', port=443): Max retries exceeded with url: /data/nccf/com/href/ (Caused by ConnectTimeoutError(<HTTPSConnection(host='ftp.ncep.noaa.g",
  "n": 0,
  "entries": []
 },
 "https://nomads.ncep.noaa.gov/pub/data/nccf/com/": {
  "url": "https://nomads.ncep.noaa.gov/pub/data/nccf/com/",
  "status": 200,
  "n": 73,
  "entries": [
   "/pub/data/nccf/",
   "557ww/",
   "aigefs/",
   "aigfs/",
   "amsu_estimation/",
   "aqm/",
   "arch/",
   "blend/",
   "ccpa/",
   "cfs/",
   "...",
   "hafs/",
   "hgefs/",
   "hiresw/",
   "hmon/",
   "hourly/",
   "href/",
   "hrrr/",
   "hur/",
   "hwrf/",
   "hycom/",
   "hysplit/",
   "ingest/",
   "lmp/",
   "naefs/",
   "nam/",
   "nam_mos/",
   "navgem/",
   "navo/",
   "ncom/",
   "ngac/",
   "nhc/",
   "nldas/",
   "nos/",
   "nosofs/",
   "nsst/",
   "nwm/",
   "nwps/",
   "obsproc/",
   "omb/",
   "para/",
   "pcpanl/",
   "petss/",
   "psurge/",
   "rap/",
   "refs/",
   "rrfs/",
   "rtma/",
   "rtofs/",
   "seaice_analysis/",
   "seaice_drift/",
   "spc_post/",
   "sref/",
   "stofs/",
   "swmf/",
   "ukmet/",
   "urma/",
   "uvi/",
   "wfs/",
   "wsa_enlil/"
  ]
 },
 "grib filter page": {
  "status": 200
 },
 "aws noaa-href-pds": {
  "bucket": "noaa-href-pds",
  "prefix": "",
  "status": 404,
  "error": [
   "NoSuchBucket"
  ],
  "prefixes": [],
  "keys": []
 },
 "aws noaa-hrefv3-pds": {
  "bucket": "noaa-hrefv3-pds",
  "prefix": "",
  "status": 404,
  "error": [
   "NoSuchBucket"
  ],
  "prefixes": [],
  "keys": []
 },
 "aws noaa-nws-href-pds": {
  "bucket": "noaa-nws-href-pds",
  "prefix": "",
  "status": 404,
  "error": [
   "NoSuchBucket"
  ],
  "prefixes": [],
  "keys": []
 },
 "aws noaa-href-conus-pds": {
  "bucket": "noaa-href-conus-pds",
  "prefix": "",
  "status": 404,
  "error": [
   "NoSuchBucket"
  ],
  "prefixes": [],
  "keys": []
 }
}
```

## WPC

```
{
 "2p5km_qpf n files": 794,
 "2p5km_qpf prefixes": [
  "p06m",
  "p120m",
  "p168m",
  "p24m",
  "p48m"
 ],
 "2p5km_qpf p06m sample": [
  [
   "p06m_2026112000f006.grb",
   "</td><td align=\"right\">19-Nov-2026",
   "21:51"
  ],
  [
   "p06m_2026112000f012.grb",
   "</td><td align=\"right\">19-Nov-2026",
   "21:52"
  ],
  [
   "p06m_2026112000f018.grb",
   "</td><td align=\"right\">19-Nov-2026",
   "21:54"
  ],
  [
   "p06m_2026112000f024.grb",
   "</td><td align=\"right\">19-Nov-2026",
   "21:56"
  ],
  [
   "p06m_2026112000f030.grb",
   "</td><td align=\"right\">19-Nov-2026",
   "21:51"
  ],
  [
   "p06m_2026112000f036.grb",
   "</td><td align=\"right\">19-Nov-2026",
   "21:53"
  ]
 ],
 "2p5km_qpf p01m sample": [],
 "2p5km_qpf issuances present": [
  "2026111212",
  "2026111300",
  "2026111312",
  "2026111400",
  "2026111412",
  "2026111500",
  "2026111512",
  "2026111600",
  "2026111612",
  "2026111700",
  "2026111712",
  "2026111800",
  "2026111812",
  "2026111900",
  "2026111912",
  "2026112000",
  "2026112006",
  "2026112012",
  "2026112018",
  "2026112100",
  "2026112106",
  "2026112112",
  "2026112118",
  "2026112200",
  "2026112206",
  "2026112212",
  "2026112218",
  "2026112300",
  "2026112306",
  "2026112312",
  "2026112318",
  "2026112400",
  "2026112406",
  "2026112412",
  "2026112418",
  "2026112500",
  "2026112506",
  "2026112512",
  "2026112518",
  "2026112600"
 ],
 "wpc qpf root": {
  "url": "https://ftp.wpc.ncep.noaa.gov/",
  "status": 200,
  "n": 178,
  "entries": [
   "2p5km_qpf/",
   "3Day_Excessive_Rainfall_Outlook.kmz",
   "5km_94e/",
   "5km_98e/",
   "5km_99e/",
   "5km_archivepop/",
   "5km_d4/",
   "5km_d5/",
   "5km_day2-3/",
   "5km_day4-5/",
   "...",
   "temp/",
   "test_2p5km_pqpf/",
   "The%20Extreme%20Flash%20Flood%20Event%20of%20Aug%201.ppt",
   "tnqpfs/",
   "tpc/",
   "tpc2/",
   "tpc_backup_scripts_2013.tar.gz",
   "tropical_advisory_archive/",
   "veenhuis/",
   "verif_excel/",
   "vgf/",
   "video/",
   "wdiment/",
   "weiss/",
   "westcoast.tar",
   "wgrfc/",
   "wh_images/",
   "winter/",
   "winwx_impact/",
   "workoff/",
   "wr_dsqpf_vs_st4qpe/",
   "wr_dwnscld_wpcqpf/",
   "WSSI_Archive/",
   "wssi_grib2/",
   "wssi_p/",
   "wssi_tiff_archive/",
   "wwo/",
   "younker/",
   "zelinsky/"
  ]
 },
 "wpc 5km_qpf": {
  "url": "https://ftp.wpc.ncep.noaa.gov/5km_qpf/",
  "status": 200,
  "n": 720,
  "entries": [
   "/",
   "p06m_2026111818f006.grb",
   "p06m_2026111818f012.grb",
   "p06m_2026111818f018.grb",
   "p06m_2026111818f024.grb",
   "p06m_2026111818f030.grb",
   "p06m_2026111818f036.grb",
   "p06m_2026111818f042.grb",
   "p06m_2026111818f048.grb",
   "p06m_2026111818f054.grb",
   "...",
   "p168m_2026111100f168.grb",
   "p168m_2026111112f168.grb",
   "p168m_2026111200f168.grb",
   "p168m_2026111212f168.grb",
   "p168m_2026111300f168.grb",
   "p168m_2026111312f168.grb",
   "p168m_2026111412f168.grb",
   "p168m_2026111500f168.grb",
   "p168m_2026111512f168.grb",
   "p168m_2026111600f168.grb",
   "p168m_2026111612f168.grb",
   "p168m_2026111700f168.grb",
   "p168m_2026111712f168.grb",
   "p168m_2026111800f168.grb",
   "p168m_2026111812f168.grb",
   "p168m_2026111900f168.grb",
   "p168m_2026111912f168.grb",
   "p168m_2026112000f168.grb",
   "p168m_2026112012f168.grb",
   "p168m_2026112100f168.grb",
   "p168m_2026112112f168.grb",
   "p168m_2026112200f168.grb",
   "p168m_2026112212f168.grb",
   "p168m_2026112300f168.grb",
   "p168m_2026112312f168.grb",
   "p168m_2026112400f168.grb",
   "p168m_2026112412f168.grb",
   "p168m_2026112500f168.grb",
   "p168m_2026112512f168.grb"
  ]
 },
 "wpc grib (ndfd-style) dir": {
  "url": "https://ftp.wpc.ncep.noaa.gov/grib/",
  "status": 200,
  "n": 22,
  "entries": [
   "/",
   "20240403/",
   "20240404/",
   "20240405/",
   "20240406/",
   "20240407/",
   "20240610/",
   "20261111/",
   "20261112/",
   "20261113/",
   "20261114/",
   "20261115/",
   "20261116/",
   "20261117/",
   "20261118/",
   "20261119/",
   "20261120/",
   "20261121/",
   "20261122/",
   "20261123/",
   "20261124/",
   "20261125/"
  ]
 },
 "ncep ftp wpc": {
  "url": "https://ftp.ncep.noaa.gov/data/nccf/com/wpc/",
  "status": "error ConnectTimeout: HTTPSConnectionPool(host='ftp.ncep.noaa.gov', port=443): Max retries exceeded with url: /data/nccf/com/wpc/ (Caused by ConnectTimeoutError(<HTTPSConnection(host='ftp.ncep.noaa.go",
  "n": 0,
  "entries": []
 },
 "nomads wpc parent": {
  "url": "https://nomads.ncep.noaa.gov/pub/data/nccf/com/wpc/",
  "status": 403,
  "n": 0,
  "entries": []
 },
 "wpc archives page": {
  "status": 404
 },
 "iem mtarchive wpc": {
  "url": "https://mtarchive.geol.iastate.edu/2026/11/25/",
  "status": 200,
  "n": 9,
  "entries": [
   "/2026/11/",
   "bufkit/",
   "bufr/",
   "cod/",
   "gempak/",
   "grib2/",
   "mrms/",
   "pix/",
   "text/"
  ]
 }
}
```

## NBM

```
{
 "blend.20261125/00/core/blend.t00z.core.f006.co.grib2": [
  "73:68749623:d=2026112500:APCP:surface:5-6 hour acc fcst:prob >0.254:prob fcst 255/255",
  "74:69562356:d=2026112500:APCP:surface:0-6 hour acc fcst:prob >0.254:prob fcst 255/255",
  "93:84243135:d=2026112500:APCP:surface:5-6 hour acc fcst:",
  "94:85359504:d=2026112500:APCP:surface:0-6 hour acc fcst:"
 ],
 "blend.20261125/00/core/blend.t00z.core.f006.co.grib2 bytes": "194197369",
 "blend.20261125/00/core/blend.t00z.core.f012.co.grib2": [
  "76:74243819:d=2026112500:APCP:surface:11-12 hour acc fcst:prob >0.254:prob fcst 255/255",
  "77:75082037:d=2026112500:APCP:surface:6-12 hour acc fcst:prob >0.254:prob fcst 255/255",
  "78:75956693:d=2026112500:APCP:surface:0-12 hour acc fcst:prob >0.254:prob fcst 255/255",
  "98:91494612:d=2026112500:APCP:surface:11-12 hour acc fcst:",
  "99:92640235:d=2026112500:APCP:surface:6-12 hour acc fcst:"
 ],
 "blend.20261125/00/core/blend.t00z.core.f012.co.grib2 bytes": "202623402",
 "oldest day": {
  "bucket": "noaa-nbm-grib2-pds",
  "prefix": "blend.2020",
  "status": 200,
  "error": [],
  "prefixes": [
   "blend.2020",
   "blend.20200518/",
   "blend.20200519/",
   "blend.20200520/",
   "blend.20200521/",
   "blend.20200522/"
  ],
  "keys": []
 }
}
```

## CNRFC

```
{
 "cnrfc qpf page": {
  "url": "https://www.cnrfc.noaa.gov/qpf.php",
  "status": 200,
  "n": 414,
  "entries": [
   "/css/cnrfc.css?random=1356057228",
   "/css/weatherstyle.css?random=199588380",
   "/css/template.css",
   "/css/ForecastSearch.css",
   "/css/search.css",
   "/includes/accordion.css",
   "/includes/jqueryui-WRU.css",
   "/favicon-32x32.png",
   "/android-chrome-192x192.png",
   "/favicon-96x96.png",
   "...",
   "https://twitter.com/nwscnrfc",
   "https://www.facebook.com/NWSCNRFC",
   "http://www.youtube.com/user/NWSCNRFC",
   "http://www.weather.gov/rss_page.php?site_name=cnrfc",
   "http://www.usa.gov",
   "http://www.commerce.gov",
   "http://www.noaa.gov",
   "http://www.weather.gov",
   "/",
   "http://www.weather.gov/disclaimer",
   "http://www.cio.noaa.gov/Policy_Programs/info_quality.html",
   "http://www.weather.gov/help",
   "http://www.weather.gov/glossary",
   "/links2.php",
   "http://www.weather.gov/privacy",
   "http://www.rdc.noaa.gov/~foia",
   "http://www.weather.gov/about",
   "http://www.weather.gov/careers",
   "http://statcounter.com/"
  ]
 },
 "cnrfc data dir": {
  "url": "https://www.cnrfc.noaa.gov/data/",
  "status": 403,
  "n": 0,
  "entries": []
 },
 "cnrfc qpf grids": {
  "url": "https://www.cnrfc.noaa.gov/data/qpf/",
  "status": 404,
  "n": 0,
  "entries": []
 },
 "cnrfc csv dir": {
  "url": "https://www.cnrfc.noaa.gov/csv/",
  "status": 403,
  "n": 0,
  "entries": []
 }
}
```

## NWS history

```
{
 "ndfd ncei": {
  "url": "https://www.ncei.noaa.gov/data/national-digital-forecast-database/access/202611/",
  "status": 404,
  "n": 0,
  "entries": []
 },
 "ndfd tgftp qpf": {
  "status": 200
 },
 "iem ndfd": {
  "url": "https://mtarchive.geol.iastate.edu/2026/11/25/model/ndfd/",
  "status": 404,
  "n": 0,
  "entries": []
 }
}
```

