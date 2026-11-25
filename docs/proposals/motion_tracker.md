# Proposal: radar motion tracker (implementation not started)

Nov 25 2026. Status: proposal for approval. Radar source (IEM N0Q mosaic) and reflectivity conversion (Z = 200R^1.6,
55 dBZ cap) stay as they are. Nothing here is implemented; the production method remains the control.

## Evidence (read-only audits: `motion_audit`, `frame_dupes`, three storms)

1. **Full-span correlation locks onto stationary structure.** In each storm 35–44 of 53 consecutive 5-minute pairs
   show ~0 km/h. About 12–14 per storm are near-duplicate frames (peak sharpness > 100); the remainder show zero shift
   while >= 35 dBZ echo moves 27–55 km/h. At Nov 24 11:05 PM the 10:45→11:05 phase peak was 0.2 km/h
   (sharpness 10.2) while every pair moved 54–62 km/h.
2. **Refinement is confined to ±8 px around that first guess.** It ended at +8.08 px, the edge of its window; that
   edge became "11 km/h toward E". The true shift was ~40 px, out of reach.
3. **Confidence never looks at the motion actually used.** "High" requires only that the pairs agree with each other
   (spread < 8 km/h), sharpness > 8 and >= 4 frames. At 11:05 PM the pairs agreed with each other (spread 4.3), but not
   with the 11 km/h the forecast used.
4. **Near-duplicate frames and stationary echo contaminate the pair statistics,** so pairs of ~0 km/h can agree with
   each other and produce "high" confidence for a near-stationary vector while steering is 30–80 km/h
   (engine < 15 km/h with 0.8 × 700 hPa wind > 30 km/h at 14 of 49 times on Nov 15, 13 of 49 on Nov 18, 2 of 49 on Nov 24).

## Proposed changes (all inside `nowcast.estimate_motion` and its helpers)

A. **Screen frames before tracking.** A pair is *near-duplicate* when its mean |dBZ| change over echo is < 1.5 dB or
   its phase-correlation sharpness is > 100 (thresholds from `frame_dupes`, fixed before testing). Near-duplicate
   frames are dropped from the stack (the pair's time interval is merged into the next pair), never counted as "no
   motion".

B. **Remove stationary structure.** Track the departure from the stack's per-pixel minimum (echo that persists in
   every frame, e.g. clutter or a stationary coastal band, is removed), apply a Hann window to the box, and ignore
   the correlation peak within 1 px of zero shift unless it beats the best non-zero peak by a fixed margin.

C. **Estimate motion from valid pairs; use the full span to refine, not to decide.** Motion = median vector of the
   valid pair velocities. The full-span shift is then searched around the pair-median prediction
   (predicted shift = median velocity × span), with radius max(8 px, 25 % of the predicted shift). A best match on
   the edge of the search window is flagged *boundary* and the refinement is discarded (pair median kept).

D. **Confidence describes the vector actually used.** High only if all hold: >= 3 valid (non-duplicate) pairs; pair
   spread < 8 km/h; the used vector within 10 km/h of the pair median; no *boundary* flag; sharpness > 8; and within
   25 km/h or 40° of the 0.8 × 700 hPa wind (or, if it is not, at most medium and the disagreement recorded). Medium
   and low as today otherwise; low keeps the existing steering fallback.

E. **Diagnostics in the output:** pairs used/dropped and why, boundary flag, steering difference, so every motion and
   confidence word can be traced in the archive.

## Replay harness (built first, read-only)

Every 5-minute time over each storm's peak 6 h: Nov 15, Nov 18, Nov 24–25 (the windows already used), plus the 6 h
before and after each peak so light-rain and decaying echo are covered. Same archived N0Q frames for both methods.

- **M1 motion-only skill:** extrapolated accumulation over the next 60 min at the block and at 8 fixed points 5 km
  around it (fixed in advance), against radar-observed accumulation at the same points using the *same* Z-R. Z-R error
  cancels, so only motion is tested. MAE, bias, and hits/false alarms at 0.20 in/h.
- **M2 vector error:** against verifying motion of >= 35 dBZ echo measured over the *following* 30 min (information
  the tracker cannot see), and against 0.8 × 700 hPa wind as a second reference.
- **M3 confidence calibration:** share of "high" times with vector error < 15 km/h, compared with medium and low.
- **M4 stability:** share of consecutive times where speed jumps > 30 km/h or direction > 60°.

## Acceptance criteria (fixed before the candidate is run)

1. **Every storm separately:** M1 MAE at the block and over the 9 points no worse than the current tracker. Pooled
   M1 MAE improved by at least 20 %.
2. **No Nov 24-only tuning:** parameters are set once for all storms. Leave-one-storm-out: thresholds chosen on two
   storms must still pass criterion 1 on the third, for all three rotations.
3. **M2:** median vector error lower than the current tracker in every storm; times with engine < 15 km/h while
   steering > 30 km/h and verifying echo > 30 km/h reduced to at most 2 per storm.
4. **M3:** "high" times with vector error > 25 km/h at most 5 % per storm. "High" error rate lower than medium's.
5. **Structural:** zero "high" outcomes with a boundary flag or with fewer than 3 valid pairs.
6. **M4:** no more unstable jumps than the current tracker in any storm.
7. **Isolation:** golden tests re-recorded with diffs confined to radar-nowcast fields; radar source and Z-R unchanged.

## Rollout options (your call)

- **Shadow first (recommended):** candidate runs beside production for the next storms, logged but not used, and is
  promoted only after it meets the criteria live as well as in replay.
- **Direct:** one PR implementing A–E once the replay passes, not merged without approval.

Step 1 either way: the replay harness and the current tracker's baseline numbers (read-only, `audit-nov24`).
