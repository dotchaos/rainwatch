"""How often does downtown SF get a day this wet? Daily totals, NOAA ACIS (USW00023272), 1991-now.

    python tools/dayscale.py > dayscale.md
"""
import sys
from datetime import date
sys.path.insert(0, ".")
from rainwatch.net import session  # noqa: E402

S = session("rainwatch day scale (github.com/dotchaos/rainwatch)")
r = S.post("https://data.rcc-acis.org/StnData", json={"sid": "USW00023272", "sdate": "1991-01-01",
           "edate": date.today().isoformat(), "elems": [{"name": "pcpn"}]}, timeout=120)
days = {}
for d, v in r.json()["data"]:
    try:
        days[d] = 0.0 if v == "T" else float(v)
    except ValueError:
        pass
yrs = (date.fromisoformat(max(days)) - date.fromisoformat(min(days))).days / 365.25
print(f"# Downtown SF daily rain, {min(days)} to {max(days)} ({yrs:.1f} years, {len(days)} days with data)\n")
print("| Day total at least | Days | Per year (avg) |\n|---|---|---|")
for t in (0.10, 0.25, 0.50, 0.75, 1.00, 1.50, 2.00, 2.50, 3.00):
    n = sum(v >= t for v in days.values())
    print(f"| {t:.2f}\" | {n} | {n / yrs:.1f} |")
print("\n## Known flood days at 17th & Folsom\n")
for d in ("2012-12-02", "2014-12-02", "2014-12-03", "2014-12-11", "2016-12-15", "2022-12-31", "2023-01-01"):
    print(f"- {d}: {days.get(d, 'missing')}\"")
top = sorted(days.items(), key=lambda x: -x[1])[:15]
print("\n## Wettest days\n")
for d, v in top:
    print(f"- {d}: {v:.2f}\"")
