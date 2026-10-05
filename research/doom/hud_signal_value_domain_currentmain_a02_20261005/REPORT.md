# HUD signal value-domain successor on current main

Disposition: `PASS_SCOPED` for the MAP01 numeric admission boundary. This is
not a live gameplay result, and it does not authorize merging or deleting the
predecessor branch.

## H / T / D / C / U

- **H:** MAP01 health is valid only in 1–200 and ammo only in 0–999. Current
  source refresh, action-source contract, action snapshot, and typed-observation
  publication must all reject an observed value outside those domains; an
  invalid source value must not be refreshed away or admitted to action state.
- **T:** Exercise out-of-domain health 201 and ammo 1000 at each of the four
  current-main boundaries. Require source refresh refusal before any send,
  contract/snapshot refusal, and typed-observation refusal before producing an
  event. Keep existing unknown, stale-binding, release, and action-admission
  behavior covered by the neighboring tests.
- **D:** Frozen source base `c1d03aca16ba4d3ffcc6c63b907a6fc11a91be5d`;
  predecessor PR #7596 head `0607bfcab46824855aedd0d0963284f796e2f023`.
  Before implementation, the source-refresh/action-contract regression run
  failed on both high values at both boundaries (4 failing subcases). The
  snapshot/typed-observation regression run then failed on the same 4 subcases.
  Added one immutable shared domain predicate and applied it at those four
  boundaries, without importing the predecessor's broader V39 controller
  rewrite. The final focused suite passed 30/30; byte-compilation and
  `git diff --check` passed.
- **C:** These are deterministic CPU-only synthetic signal values. The limits
  follow the MAP01-specific proposal: health-policy schema 1–200 and the
  three-slot ammo display 0–999. Existing HASH/WAD readers, controller
  behavior, prior evidence, and failed/STOP records are unchanged. The old
  branch's full tree conflicts with current main in typed-observation and
  V39-controller files and removes current protections; this successor does
  not copy those deletions.
- **U:** No real HUD frame, WAD recognition accuracy, game/model/GPU/GUI/live
  input, recovery efficacy, useful feedback, task completion, latency, or
  performance was tested. This is not full-repository CI. The container path
  stopped before invocation: `docker images` failed because the daemon's
  containerd content-store blob read returned `operation not supported`. Tests
  ran locally in a temporary Python 3.12.13 venv with Pillow 11.3.0, pinned to
  the repository workflow's declared version. GitHub Actions and independent
  review remain separate gates.

## Reproduction

```text
PYTHONPATH=research/doom:research/live_control \
  /tmp/unjuno-7596-venv.FQAZm0/bin/python -m unittest \
  research.doom.test_source_refresh_v1 \
  research.doom.test_doom_action_validity_contract_v1 \
  research.doom.test_doom_action_snapshot_v1 \
  research.doom.test_doom_typed_observation_v1 \
  research.live_control.test_action_validity_admission_v1
  PASS 30/30

/tmp/unjuno-7596-venv.FQAZm0/bin/python -m py_compile \
  research/doom/doom_signal_value_domain_v1.py \
  research/doom/doom_source_refresh_v1.py \
  research/doom/doom_action_validity_contract_v1.py \
  research/doom/doom_action_snapshot_v1.py \
  research/doom/doom_typed_observation_v1.py
  PASS

git diff --check
  PASS
```

The predecessor PR #7596 remains unchanged and open. Its content, reviews, and
checks do not transfer to this successor. No remote branch was deleted.
