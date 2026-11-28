"""Read-only: show the raw WPC QPF directory listing format and per-issuance file inventory."""
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bench.net import Net  # noqa: E402

r, _ = Net().get("https://ftp.wpc.ncep.noaa.gov/2p5km_qpf/")
t = r.text
i = t.find("p06m_")
print("# WPC listing format\n\n```\n" + t[max(0, i - 600):i + 900] + "\n```\n")
by = defaultdict(lambda: defaultdict(list))
for n in set(re.findall(r'href="(p\d+m_\d{10}f\d{3}\.grb2?)"', t)):
    m = re.match(r"p(\d+)m_(\d{10})f(\d{3})", n)
    by[m.group(2)][f"p{m.group(1)}m"].append(int(m.group(3)))
print("| issuance | products: first-last fh (count) |\n|---|---|")
for iss in sorted(by):
    print(f"| {iss} | " + "; ".join(f"{k} f{min(v):03d}-f{max(v):03d} ({len(v)})" for k, v in sorted(by[iss].items())) + " |")
