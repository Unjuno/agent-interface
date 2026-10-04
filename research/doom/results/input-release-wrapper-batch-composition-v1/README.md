# Retained wrapper and release-batch composition v1

## Frozen question and gate

- **H:** the retained batch adapter consumes the actual v3 per-key wrapper
  receipt correctly and publishes one verified batch row only after the
  post-batch owner sample.
- **T:** invoke one explicit key-up through the retained adapter's real `raw`
  implementation and the actual `input_transition_owner_v3.py` wrapper, with
  an injected in-memory owner beneath that wrapper.
- **D:** require matching nonempty owner/intent identities, a monotonic
  key-up-return then state-sample order, one row for the one-key batch, and
  `owner_transition_verified=true` only with empty owned state. Any mismatch
  fails the experiment.
- **C:** synthetic in-memory owner only. No X server, OS input, game, model,
  display server, or container is started. The fake parent class is the unit
  harness; the release adapter source and v3 wrapper source are the code paths
  under test.
- **U:** schema/composition compatibility only. This does not verify physical
  release, application consumption, useful feedback, recovery, or a live MAP01
  outcome.

Frozen implementation at start (`76e536c5c3b81eb66864c4bbe27f16c229ebf3a9`):

| Source | SHA-256 |
|---|---|
| `research/doom/doom_retained_input_backend_v3.py` | `1b96e852fa5da4cee531bdcb4832345a1f8355574bdcaa87665ac50c667b9f55` |
| `research/live_control/input_transition_owner_v3.py` | `5ffdbb3679451fefdc3836917d43d924f0f43c8082d21327207ecefbd87f5be6` |
| `research/doom/test_doom_retained_input_backend_v3.py` before test addition | `f210cc2cb4b360f6f925fe33cf06d9c0eaff34bd6e3da1e215374c4204d335b9` |

The first attempt stopped before candidate execution due to a missing test
harness import; its output is preserved in `first-attempt.txt`. The harness
repair imported `patch` explicitly and did not alter either frozen implementation
source.

## Reproduction

From the repository root:

```text
python -m unittest research.doom.test_doom_retained_input_backend_v3.Tests.test_batch_adapter_accepts_actual_v3_wrapper_receipt -v
python research/doom/results/input-release-wrapper-batch-composition-v1/capture_candidate.py
python research/doom/results/input-release-wrapper-batch-composition-v1/audit_candidate.py
```

The exact receipt is in `candidate.json`, candidate stdout in
`candidate-stdout.json`, and the independent field/order audit in `audit.json`
plus `audit-stdout.json`. The audit reads the retained JSON without calling the
candidate generator, checks release and sample timestamp order, and recomputes
the two frozen implementation source hashes.

Local verification after the harness repair:

```text
python -m unittest research.doom.test_doom_retained_input_backend_v3 -q  # 15/15 PASS
python -m unittest research.live_control.test_input_transition_owner_v3 -q  # 8/8 PASS
python -m unittest research.doom.test_map01_overlap_controller_v40 -q  # 3/3 PASS
git diff --check  # PASS
```

No live or model allocation was used. The shared WSLc lane remains a separate
gate for live threat exposure, useful-feedback measurement, recovery, and
matched-condition claims.
