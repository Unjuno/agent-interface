# V39 retained model-pending HUD trajectory posthoc A01

## H / T / D / C / U

**H.** The retained real MAP01 V39 coast-liveness run has 218 paired typed observations and six model-pending windows. Prior issue analysis discussed selected events from decision 5; it did not publish a complete reconstruction of all six intervals using each decision's admitted source signal and planner terminal timestamp.

**T.** Freeze the retained report and event streams by SHA-256, independently reconstruct every health/ammo change from the admitted source observation through planner terminal, list authored hard-threshold crossings, and verify that delivered events match the source event stream. Do not run or modify the game, model, GUI, controller, or historical results.

**D.** PASS when all 218 typed observations have contiguous sequence IDs and matching paired signals, source/delivered streams are byte-semantically identical, six source-to-terminal windows reconstruct exactly, threshold crossings match an independent audit, and changed result/input data is rejected.

**C.** The reconstruction finds health loss during five of six model waits and ammo consumption during four. In decision 1, health reaches its authored hard floor of 85 (a 12-point loss from source); in decision 5, it reaches the hard floor of 51 (a 10-point loss) and later falls below it to 48. Decision 4 declines from 65 to 64/61, a 1/4-point loss that remains within its authored maximum loss of 10 and above its hard floor of 55. The retained report records one policy invalidation overall. This establishes an evidence gap inside the retained episode, not what a fresh current-main controller would do.

**U.** HUD-derived health/ammo are not independent game-state ground truth. Timing association does not prove causality. The historical run ended alive but unfinished, with no exit and no useful recovery/task completion. A fresh current-main live threat run with useful recovery and a subsequent MAP01 outcome remains outstanding and separately gated.

## Reproduced trajectory

| Decision | Source seq / health | Pending observations through | Health / ammo changes during pending |
|---:|---:|---:|---|
| 0 | 1 / 97 | 28 | none (97/48) |
| 1 | 36 / 97 | 70 | seq37 91/46; seq47 91/45; seq62 85/45 (hard floor); seq64 85/44 |
| 2 | 70 / 85 | 91 | seq76 82/44; seq81 76/44; seq90 73/44 |
| 3 | 91 / 73 | 113 | seq97 72/44; seq103 68/44 |
| 4 | 115 / 65 | 159 | seq125 65/42; seq143 65/41; seq144 64/41; seq154 61/41 (below hard floor 55) |
| 5 | 166 / 61 | 218 | seq167 55/40 (~241 ms); seq177 55/39; seq193 52/39; seq194 52/38; seq200 51/38 (floor); seq212 51/37; seq218 48/37 |

The six planner calls lasted 8.452, 5.720, 6.307, 6.725, 7.198, and 8.916 seconds by the report's `model_ns` measure. Capture timestamps through terminal are separately reconstructed in `RESULT.json`; the differing figures reflect the model timing field versus source-to-terminal interval.

## Reproduce

Run `python analyze.py`, then `python audit.py`, then `python -m unittest discover -s tests -v` from this directory. Run the same test command with `python -O` as a second check. Inputs are frozen copies of the retained `report.json`, `runtime/events.jsonl`, and `runtime/delivered.jsonl`; `RESULT.json` records their hashes. No game/model/controller/GUI/OS input was invoked.
