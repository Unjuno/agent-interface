# Issue #6664 — observable quiescence certificate T0

Finite deterministic protocol-model experiment only. It does not run or control a GUI, OS input backend, model, participant, container, or production runtime.

`scenarios.py` freezes a finite family of event schedules around takeover. `candidate.py` compares epoch-only, a fixed grace delay, and a ledger/receipt-based quiescence policy. `auditor.py` independently reconstructs policy claims from each schedule's raw event list; it imports neither candidate nor its decision functions. The scenario generator is the fixture source and is hashed in `FREEZE.json`.

The Issue explicitly says no container allocation is authorized or required. This pure standard-library protocol model therefore runs on host CPython 3.14.5; it makes no OrbStack/WSLc claim. The result cannot establish actual backend cancellation, OS queues, application effects, human takeover safety, or portability.
