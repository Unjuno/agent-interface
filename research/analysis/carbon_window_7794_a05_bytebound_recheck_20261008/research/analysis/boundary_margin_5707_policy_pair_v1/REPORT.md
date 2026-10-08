# Issue #5715 / #5707 paired-policy T0

**Disposition: `PASS_METHOD_SCOPED`.** Two distinct fixed policies received the same four exogenous opportunity IDs, boundaries and external hazard/event records. Both had zero forbidden effects; raw-only reconstruction found minimum admission-to-boundary slack of 60 ms for `early` and 10 ms for `late`. The ledger distinguished the constructed margin contrast without changing the event-only count. This is a synthetic method result only.

## Frozen method and identities

Successor Issue #5715 directly addresses #5709's retained method failure: `comfortable` and `thin` had been separate scenario labels rather than policy arms. The corrected experiment freezes both actual arms on identical opportunity identities `opp-01..opp-04`, boundary times 100/200/300/400 ms, and the same external event IDs/times. `early` admissions are 40/140/240/340 ms; `late` are 90/190/290/390 ms. The auditor derives each margin as boundary minus admission, and independently checks both arms and the common event schedule.

Publication base: `dc53e1ac7def5b150809dbfe3d4c910d66a85fa0`; branch `research/5707-policy-pair-t0-20261001`; image `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`; networking disabled. Source Git blob IDs and SHA-256 pins are in `MANIFEST.json` and were read back from GitHub before execution.

## Execution and audit

The preflight suite ran in a read-only, network-disabled OrbStack container before formal execution: 6/6 passed, including mutations to admission timestamp, opportunity identity, external event identity, crossing sign, and missing timestamp.

The frozen runner ran exactly once in a read-only container with a separate writable output mount; exit status 0. Six JSONL records were emitted. The raw-only auditor then ran separately, network-disabled and read-only, and returned `PASS_METHOD_SCOPED`, 6 rows, no errors. Raw JSONL SHA-256: `bdb2edc6e9653dafb17898d5569e3dc3afe71927ec25c00b4b060528fd639e88`.

Observed frozen controls:

- Matched pair: 4/4 identical opportunity IDs and external event records per arm; forbidden effects 0/0; all `early` margins 60 ms and all `late` margins 10 ms.
- Crossing: -3 ms and forbidden effect true, classified `BOUNDARY_CROSSED`.
- Safe stop: retained as `STOP_RECORDED_OUTCOME_UNKNOWN`; no claim that the world stayed safe.
- Missing admission time: `UNKNOWN`.
- Changed opportunity identity: `HOLD_NO_STABLE_DENOMINATOR`.
- Exact equality: zero margin and `ZERO_MARGIN_NOT_CROSSED`.

## Scope and uncertainty

This supports only that, in this deterministic fixture, the raw ledger/auditor can distinguish two authored admission schedules with equal event-only counts on a fixed opportunity set and can preserve the declared negative controls. It does not validate real clock alignment, an application or backend, natural near-miss prevalence, harm prediction/calibration, safety benefit, or policy choice. The margin is diagnostic and does not grant authority. No production or ROADMAP runtime gate is closed.
