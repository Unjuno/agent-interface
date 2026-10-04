# Session-bound scorer attribution v2 — H/T/D/C/U

Parent: scorer-attribution construction PR #7537, frozen at `b076890cbcd28f2889184055453f2868fd87c629`.

**H.** The v1 temporal join can accept a scorer event and input interval from different runs when their numeric monotonic timestamps happen to overlap, because its record contract does not require a shared session identity. Requiring one non-empty `session_id` across samples, events, and intervals should reject that false join while preserving a fully covered same-session association.

**T.** Use fixed hand-authored rows: scorer samples `[100, 200]` and a positive event at `200` belong to `run-b`; a verified intent interval `[90, 210]` belongs to `run-a`. First run the frozen v1 implementation as the adversarial control, then the v2 wrapper. Also check same-session preservation and missing identity refusal. No timestamps are sampled from a live clock.

**D.** `PASS_SESSION_BOUND` iff frozen v1 returns `TEMPORALLY_UNIQUE` for the cross-session control, v2 rejects that mismatch and any missing session identity, and v2 still returns the same scoped temporal association for same-session rows. A v2 output never establishes causation.

**C.** This demonstrates an API-level false-join possibility, not that existing live logs are mixed. It does not prove a session ID is authentic; a future integrated collector must bind it to one frozen session and clock source. V2 delegates unchanged timing semantics to v1.

**U / STOP.** No retained live outcomes, game, model, GUI, physical input, useful task effect, recovery, or allocation was used. Docker is present but image-store listing fails with `operation not supported`; no eligible isolated container run was possible. The #59 live allocation remains unassigned.

## Commands

From this directory:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.. python3 -B -m unittest discover -s . -v
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.. python3 -B run_t0.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.. python3 -B audit.py
```
