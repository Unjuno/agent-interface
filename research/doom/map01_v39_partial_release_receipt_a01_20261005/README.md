# V39 partial per-key release receipt A01

## Result

The pinned #7847 candidate baseline loses the already confirmed F8 key-up
receipt when the second of two held-key releases raises: the owner has no
`owner_release` row, so the bridge emits no F8 release row. The candidate
versioned here persists one partial `owner_release` before propagating the
exception. The raw fake-display result retains F8's original admission identity
and confirms its per-key UP, keeps the aggregate release unverified, leaves F9
down in both fake and bridge state, and rejects later input before injection.
The raw-only auditor independently checks source pins, the pre-fix RED output,
the post-fix GREEN output, row identity, physical sample states, event ordering,
bridge custody, and fail-closed state.

## H / T / D / C / U

See `PREREGISTRATION.md` and `FREEZE.json`. This is a deterministic candidate
construction result against the fake display used by the #7847/V39 bridge
tests. It does not establish real X11 or application delivery. The confirmed
state transition is sampled in the harness; it is not an application effect.

## Reproduction

From the repository root at the stacked #7847 candidate revision:

```sh
V13_OWNER_CANDIDATE_PATH=research/doom/map01_v39_cancel_release_fix_a01_20261005/input_owner_v13_candidate.py \
  python3 -m unittest research.doom.map01_v39_partial_release_receipt_a01_20261005.test_partial_release_receipt -v
python3 -m unittest research.doom.map01_v39_cancel_release_fix_a01_20261005.test_cancel_release -v
python3 -O -m unittest research.doom.map01_v39_cancel_release_fix_a01_20261005.test_cancel_release -v
python3 research/doom/map01_v39_partial_release_receipt_a01_20261005/audit_result.py
```

The focused candidate and original candidate suite ran on macOS arm64 with the
Python runtime recorded in `FREEZE.json`; no container, game, model, GUI, OS
input, or live allocation was used. `RED_OUTPUT.txt` and `GREEN_OUTPUT.txt`
retain the focused baseline and candidate outcomes. `raw.json` retains the
candidate's structured observed state. `AUDIT.json` records the raw-only audit.

Issue #59 remains open. Threat exposure, independently useful live feedback,
bounded recovery, a separately identified MAP01 attempt, and matched live
comparison remain unverified.
