# Strip shading prototype

Run 2026-11-16 00:25 UTC. Models: ecmwf_ifs025 ensemble (51 members), gfs_seamless ensemble (31 members), icon_seamless ensemble (40 members); each stretch uses every run present for all its hours. Classes: `.` none, `L` light (<0.10"/h), `M` moderate (0.10–0.20), `H` heavy (≥0.20).

## Fri 7 AM – Fri 4 PM (9 h, past)

122 runs. Run totals: median 0.63", mean 0.61". Sum of A 0.57", sum of B 0.61". Gauge 0.6" (0 hours missing).

```
A median     LLLMMMLLL
B matched    .LLMMMLL.
C peak       MMMMMMMMM   (typical run's heaviest hour 0.16")
Gauge        LLMMML...
```

## Sun 1 PM – Sun 11 PM (10 h, forecast)

122 runs. Run totals: median 0.57", mean 0.57". Sum of A 0.52", sum of B 0.56". Gauge 0.37" (8 hours missing).

```
A median     LLLLLLLLLL
B matched    LMMLLLLL..
C peak       MMMMMMMMMM   (typical run's heaviest hour 0.11")
A at 36 h    ??????????   (archive: hourly medians saved 36 h ahead)
Gauge        MH????????
```

## Wed 1 AM – Thu 10 AM (33 h, forecast)

122 runs. Run totals: median 1.32", mean 1.56". Sum of A 1.0", sum of B 1.53".

```
A median     LLLMMMLLLLLLLLLLLLLLLLLLLLLLLLLLL
B matched    LLLHMMMMLLLLLLL.........LLLLL....
C peak       MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM   (typical run's heaviest hour 0.17")
```

