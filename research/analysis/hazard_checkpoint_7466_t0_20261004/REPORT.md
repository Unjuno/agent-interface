# Issue #7466 T0 — cost-sensitive placement construction failed

**Disposition: `FAIL_ADAPTIVE_BENEFIT_IN_THIS_CONSTRUCTION`; fallback invariant passes.** This is not a formal held-out/calibrated study and does not reject all adaptive placement policies.

The deterministic WSL2/Python 3.12.3 simulator ran 400 paired seeds per cell (2,400 rows). With the deliberately perfect periodic runtime-visible signal, adaptive placement cost 79.8425 units on average, versus 56.3525 fixed and 70.4875 event-boundary. Under an uninformative signal, adaptation abstained and exactly matched the event-boundary policy on all 400 paired seeds (67.565 mean cost). The control shows the observability fallback works in this construction, but the positive adaptive-benefit hypothesis does not: a predictive signal alone is insufficient, and the chosen placement rule schedules work poorly relative to checkpoint cost and exposure.

The raw-only audit passed row count, key uniqueness, cost reconstruction, and exact fallback equality. Detailed protocol, source/output hashes, limitations, and command are in [RUN.md](RUN.md); [README.md](README.md) states H/T/D/C/U. The complete raw data are in [raw.jsonl](raw.jsonl), with aggregates in [summary.json](summary.json).

**Scope limit:** no checkpoint serialization/verification cost, effect classes, held-out calibration, cluster-shift, live interruption distribution, runtime, or task correctness is measured. Do not promote a checkpoint policy from this probe.
