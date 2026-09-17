# INPUT-OWNER-PHYSICAL-SAMPLE-SEQUENCING-20260918-001

BASE e690e155aa00fb72a30586513caf9bfeec9a8a7d
Issue #1030. Construction only.

H: best-effort physical key-state sampling inserted inside the same serialized ordinary down/up request can be observational-only: after removing sample rows, candidate non-measurement traces/outcomes/state exactly equal the modeled v10 baseline, including sample failures.
T: exact v10 source identity + fixed adversarial cases + >=500k seeded randomized cases; independent auditor; no X11/task input.
D: PASS only on exact non-sample equivalence, required sample ordering, no sample-dependent action decision, no interval/actuation/authority claim, source/audit integrity.
C: pure model may miss Xlib side effects/cost; best-effort sampling may be unsafe/slow live.
U: no physical/X11 truth or application-consumption evidence.
