"""ERO parsing: real WPC layout (dn + OUTLOOK, POINT for 'none expected', UTC times); any doubt is 'unknown'."""
import io
import zipfile

import shapefile

from bench.settings import LAT, LON
from bench.sources import ero

GEO = 'GEOGCS["GCS_North_American_1983",DATUM["D_North_American_1983",SPHEROID["GRS_1980",6378137.0,298.257222101]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]]'
FIELDS = ["dn", "PRODUCT", "VALID_TIME", "OUTLOOK", "ISSUE_TIME", "START_TIME", "END_TIME"]


def zipped(records, prj=GEO, valid="12Z 11/29/26 - 12Z 11/30/26", start="2026-11-29 12:00:00", end="2026-11-30 12:00:00"):
    shp, shx, dbf = io.BytesIO(), io.BytesIO(), io.BytesIO()
    kind = shapefile.POINT if records and records[0][0] == "point" else shapefile.POLYGON
    w = shapefile.Writer(shp=shp, shx=shx, dbf=dbf, shapeType=kind)
    for f in FIELDS:
        w.field(f, "C", 60)
    for geom, dn, outlook in records:
        if geom == "point":
            w.point(-95.0, 38.0)
        else:
            w.poly([geom])
        w.record(str(dn), "Day 2 Excessive Rainfall Potential Forecast", valid, outlook, "2026-11-28 08:00:00", start, end)
    w.close()
    z = io.BytesIO()
    with zipfile.ZipFile(z, "w") as zf:
        for ext, b in (("shp", shp), ("shx", shx), ("dbf", dbf)):
            zf.writestr(f"x.{ext}", b.getvalue())
        zf.writestr("x.prj", prj)
    return z.getvalue()


AROUND = [(LON - 1, LAT - 1), (LON - 1, LAT + 1), (LON + 1, LAT + 1), (LON + 1, LAT - 1), (LON - 1, LAT - 1)]
AWAY = [(-100, 40), (-100, 41), (-99, 41), (-99, 40), (-100, 40)]


def test_slight_over_the_block_inside_a_marginal():
    big = [(LON - 3, LAT - 3), (LON - 3, LAT + 3), (LON + 3, LAT + 3), (LON + 3, LAT - 3), (LON - 3, LAT - 3)]
    r = ero.at_block(zipped([(big, 1, "Marginal (At Least 5%)"), (AROUND, 2, "Slight (At Least 15%)")]))
    assert (r["category"], r["category_rank"], r["problems"]) == ("slight", 2, [])
    assert r["issued_utc"] == "2026-11-28T08:00:00+00:00" and r["valid_start"] == "2026-11-29T12:00:00+00:00"


def test_none_expected_point_and_risk_elsewhere():
    assert ero.at_block(zipped([("point", 0, "None Expected")]))["category"] == "none at the block"
    assert ero.at_block(zipped([(AWAY, 1, "Marginal (At Least 5%)")]))["category"] == "none at the block"


def test_doubt_is_unknown_never_outside():
    assert ero.at_block(b"PK not really a zip")["category"] == "unknown"
    assert ero.at_block(zipped([(AWAY, 2, "Marginal (At Least 5%)")]))["category"] == "unknown"        # dn vs label
    assert ero.at_block(zipped([(AWAY, 1, "Marginal (At Least 5%)")], prj='PROJCS["Lambert"]'))["category"] == "unknown"
    assert ero.at_block(zipped([(AWAY, 1, "Marginal (At Least 5%)")], start="2026-11-29 13:00:00"))["category"] == "unknown"
    assert ero.at_block(zipped([(AWAY, "x", "Marginal")]))["category"] == "unknown"
