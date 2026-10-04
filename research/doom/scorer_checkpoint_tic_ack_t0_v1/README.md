# Scorer checkpoint tic acknowledgment T0

Question: does the retained private score checkpoint status prove that its one-tic refresh happened and that score reads remained in the same tic?

The test executes the exact retained helper against synthetic game, owner, and executor fakes. Cases cover one acknowledged tic with stable reads, a no-op, two tics, tic drift during score reads, and an exception. The independent candidate predicate requires a nonnegative integer `tic_before`, `tic_after == tic_before + 1`, and `tic_after_read == tic_after`, in addition to the helper’s pending status. The synthetic controller gate reproduces the current status-only condition.

Observed on the frozen source pins: the helper returns `REFRESH_RETURNED_RUNTIME_QUALIFICATION_PENDING` for the no-op, two-tic, and read-drift fakes, and that status-only gate accepts all three. The candidate audit rejects all three. This is a missing acknowledgment check in a prospective draft path, not proof of source adoption, a real ViZDoom execution, episode progress, score correctness, or useful recovery.

Run from the repository root:

```powershell
python research/doom/scorer_checkpoint_tic_ack_t0_v1/run.py
python research/doom/scorer_checkpoint_tic_ack_t0_v1/audit.py
python -m unittest discover -s research/doom/scorer_checkpoint_tic_ack_t0_v1 -v
```

`raw.json` contains no score values. `source-pins.json` records exact source digests.

## Minimal repair construction test

`candidate_helper.py` is an isolated copy with two guards: the refresh must advance exactly one tic, and the tic must remain stable through the score read. `repair_run.py` runs the same five fake outcomes against that copy; `repair_audit.py` independently checks that only the valid one-tic case receives the status accepted by the controller. This tests the proposed fail-closed repair against the counterexamples above. It remains synthetic construction evidence and does not qualify a real game session.

Reproduce the repair check with `python research/doom/scorer_checkpoint_tic_ack_t0_v1/repair_run.py` and `python research/doom/scorer_checkpoint_tic_ack_t0_v1/repair_audit.py`. The retained outcome is `repair-raw.json` / `repair-audit.json`; its accepted set should contain only `one_tic_acknowledged`.
