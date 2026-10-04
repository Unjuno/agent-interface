# Owner cleanup overlap release classification v1

## Question and decision gate

- **H:** a post-request owner cleanup can empty the owner state while the v3
  wrapper still labels the queued explicit `up` ordinary at request time; the
  batch adapter then overstates that as an ordinary verified release.
- **T:** inject one deterministic explicit-up no-op whose synthetic
  `owner_release.verified_ns` falls inside the real v3 wrapper's caller bracket,
  then pass its receipt through the actual v3 batch adapter.
- **D:** overlapping cleanup must set
  `owner_cleanup_overlapped_release_call=true`, preserve the wrapper's
  request-time value separately, clear the effective
  `ordinary_release_candidate`, and force `owner_transition_verified=false`.
- **C:** the in-memory owner emits a timestamped `owner_release` record during
  the actual wrapper call; the actual wrapper/adapter source is exercised, but
  v10 queue scheduling is not. No X11 server, OS input, game, model, container,
  or live allocation is used. Race reachability is supported by the separately
  retained #59 / PR #7355 reproduction and source review.
- **U:** this control does not establish physical key-up actuation, application
  consumption, event-loop timing on a real display, useful feedback, recovery,
  or MAP01 outcome. The owner record and boundary are synthetic.

The root interleaving is already preserved independently at #59 comment
5975517341 and PR #7355 review comment 4175713389. This is a distinct
mitigation test of the v13 batch adapter; it does not repeat that owner's
baseline experiment or change the neighboring branch.

Frozen pre-fix sources at commit `b47b5281181bfc992026b021d38a6cd00a2ba26b`:

| Source | SHA-256 |
|---|---|
| `research/doom/doom_retained_input_backend_v3.py` | `1b96e852fa5da4cee531bdcb4832345a1f8355574bdcaa87665ac50c667b9f55` |
| `research/doom/test_doom_retained_input_backend_v3.py` | `abcb5ce6acb9893978207cc9f3d54dc2e2b56164e6bc2603ac23bcaf2e26a55a` |
| `research/live_control/input_transition_owner_v3.py` | `5ffdbb3679451fefdc3836917d43d924f0f43c8082d21327207ecefbd87f5be6` |
| `research/live_control/input_owner_v10.py` | `ceae7d9983cd0ba13a35e01ce2ce7dbbf03a0397b23ddc123b0110b4d4de670b` |

The first mitigation control failed against the frozen behavior because the
row remained verified; see `baseline-red.txt`. The candidate now correlates `owner_release`
timestamps from the wrapper's owner record log with each explicit-up bracket.
It retains the wrapper's request-time classification in
`ordinary_release_candidate_at_request`, sets the effective candidate false
for an overlapping cleanup, and requires the cleanup record list for a verified
batch. The clean ordinary wrapper path remains a positive control.

## Reproduction

From the repository root:

```text
python -m unittest research.doom.test_doom_retained_input_backend_v3.Tests.test_owner_cleanup_inside_up_call_is_not_verified_as_ordinary -v
python research/doom/results/input-release-owner-cleanup-race-v1/capture_candidate.py
python research/doom/results/input-release-owner-cleanup-race-v1/audit_candidate.py
```

`candidate.json` and `audit.json` retain the latest raw receipt/owner record
and independent audit. The auditor verifies that exactly one cleanup timestamp
is inside the explicit-up bracket, the request snapshot was stale-ordinary, the
adapter reclassified it, no authority claim was made, and the source hashes
match the candidate freeze. A post-rebase package-integrity refresh generated a
second deterministic fixture receipt with new monotonic timestamps; the prior
receipt/audit/stdout are preserved as `*-initial.json`, and the refreshed ones
are preserved in the primary files. This was construction harness verification,
not another live allocation or physical-input run.

Post-fix local verification:

```text
python -m unittest research.doom.test_doom_retained_input_backend_v3 -q  # 18/18 PASS
python -m unittest research.live_control.test_input_transition_owner_v3 -q  # 8/8 PASS
python -m unittest research.doom.test_map01_overlap_controller_v40 -q  # 3/3 PASS
git diff --check  # PASS
```

This does not replace the separately gated live/X11 validation. The existing
owner-thread timing, physical key state, useful feedback, bounded recovery,
matched comparison, and full MAP01 gates remain open.
