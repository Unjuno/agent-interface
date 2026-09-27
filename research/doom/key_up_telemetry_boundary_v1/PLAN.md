# #4130 key-up telemetry boundary — H/T/D/C/U freeze

H: owner/program/step/key-bound receipt emitted only after KeyRelease XTEST + XSync can expose acknowledged up time without changing input behavior.
T: BASELINE vs KEY_UP_RECEIPT; four schedules; three reps =24 fresh sessions; private Xvfb; no model/game.
D: exact 24 rows, neutral endpoints, candidate receipt exactly per admitted key, no receipt for unadmitted key, same X event cardinality; independent raw audit and corruption controls.
C: X server logical state only; directed barriers; no production/runtime promotion.
U: impact on v38/v39 interval width and task usefulness remain untested.

Formal command: `python -B run_matrix.py --out <absent-formal-dir> --reps 3` exactly once after public source hash freeze/readback.
