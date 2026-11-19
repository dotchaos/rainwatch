"""Archive the published live card exactly as served (Nov 19): fetches https://dotchaos.github.io/rainwatch/live.json and
writes it unchanged to archive_live.json (the analysis workflow copies that to the data branch). Used to make timestamped
fixtures from real published cards; prints the card's generated time and a SHA-256 of the bytes."""
import hashlib, json, sys, urllib.request

URL = "https://dotchaos.github.io/rainwatch/live.json"
raw = urllib.request.urlopen(f"{URL}?t=archive", timeout=30).read()
card = json.loads(raw)
open("archive_live.json", "wb").write(raw)
print(f"# Archived live card\n\n- URL: {URL}\n- generated: {card['provenance']['generated']}\n- observedAt: {card['observedAt']}\n"
      f"- sha256: {hashlib.sha256(raw).hexdigest()}\n- bytes: {len(raw)}")
