# Frozen fixed-threat natural invalidation run on v28

`map01-fixed-threat-v28-live-01` is the first and only preregistered six-decision
Luna-low allocation from `map01-threat-contact-v1`. The runtime receipt verifies
the fixture manifest and save hashes and restores real Freedoom MAP01 episode
tic 1263 before measured control. The allocation's exact initial frame visibly
contains an enemy at health 100 and ammunition 50.

Natural HUD-region changes invalidate decisions 0, 2, 3, 4, and 5. All five
matching planner turns receive one typed interrupt, complete as interrupted,
and remain ineligible. Their dependent actions admit no plan input. All six
cover programs and the one admitted plan program terminate with verified empty
key/button release. Decision 1 recovers on the same app-server thread after the
first interrupt, completes a typed `advance_fire` plus `strafe_left` action, and
authors a nonempty threat cover. Decision 2 starts that cover, then a further
natural damage change cancels it and discards the dependent turn. Decision 3
inherits no cover from the discarded result. This is the first natural exposure
of the complete stale nonempty-cover invalidation path in the current interface.

The retained reviewed health sequence is 100, 97, 93, 87, 81, 79, 73; every
reviewed frame visibly contains an enemy. Detection-to-interrupt-send takes
0.026–0.324 ms, interrupt-send-to-ack 1.751–3.379 ms,
interrupt-send-to-completion 2.342–4.201 ms, and detection-to-cover-release
20.435–25.048 ms across the five events. Capture-to-detection is
83.133–154.506 ms and includes queue/dequeue plus region evaluation.

The safety mechanism also exposes a liveness defect: five of six high-level
decisions are interrupted. Replanning on every qualifying damage-region change
can starve the planner during sustained combat. A bounded local cover should be
allowed to absorb some expected threat evolution while high-level interruption
is reserved for changes that invalidate the cover's assumptions. This result
does not yet identify that semantic boundary.

Four token-usage notifications carry one identical receipt. The only
attributable known receipt is 9,351 input tokens, including 7,936 cached, plus
168 output and 62 reasoning tokens for the completed turn. Interrupted-turn
usage is unknown and must not be treated as zero or summed from the repeated
cumulative receipt.

Measured control lasts 17.414 seconds and model wall intervals total 14.355
seconds. The independent score is alive and unfinished with zero kills, deaths,
or exit. This is mechanism and failure-discovery evidence, not a survival,
gameplay-quality, token-efficiency, reliability, human-speed, or MAP01-clear
claim.

Run the retained audit with:

```sh
python research/doom/audit_map01_fixed_threat_v28_live_v1.py
```
