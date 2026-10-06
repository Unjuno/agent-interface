# Current v39 per-key release telemetry port — construction HOLD

This additive port brings the retained v13 non-staggering per-key release
adapter onto the exact backend selected by the retained v39 source closure.
`session_map01_v12.py` now selects `doom_typed_release_backend_v3.py`; that
adapter differs from `doom_retained_input_backend_v3.py` only in inheriting the
current `doom_typed_release_backend_v1` base. Its release owner remains the
current `InputOwner v10` wrapped by `input_transition_owner_v3`.

## H / T / D / C / U

- **H:** Current v39 can retain a caller-timed per-key explicit-up bracket while
  preserving the tested non-staggering batch rule: complete all explicit key
  ups, take one owner-state sample, then publish the per-key records.
- **T:** Check the exact current-v39 runtime source closure, prove the adapter
  is a one-import change from the previously tested v3 backend, and run the
  candidate batch tests plus the retained backend/owner construction suites.
- **D — `PASS_CONSTRUCTION / HOLD_NATIVE_VALIDATION`:** 14 candidate tests,
  11 retained adapter tests, and 8 retained owner-wrapper tests pass (33 total).
  The selected session names and hashes the candidate adapter and its transition
  wrapper. Python byte-compilation and `git diff --check` pass.
- **C:** A successful owner call bracket and post-batch owned-keycode sample do
  not continuously observe physical key state or prove application consumption.
  The adapter adds one owner-state sample after a completed release batch and
  therefore may affect release-to-feedback latency.
- **U:** No ViZDoom, X11, GUI, live input, model, or container execution was
  performed. The recorded v39 session used the original v1 backend and has no
  per-key transition receipts. A freshly frozen, no-model current-v39 telemetry
  validation still needs its own disposable X11 lane and independent review.

## Reproduction

From repository root:

```sh
python3 research/doom/test_doom_typed_release_backend_v3.py
python3 research/doom/test_doom_retained_input_backend_v3.py
python3 research/live_control/test_input_transition_owner_v3.py
python3 -m py_compile research/doom/doom_typed_release_backend_v3.py research/doom/session_map01_v12.py research/doom/test_doom_typed_release_backend_v3.py
git diff --check
```

`CONSTRUCTION.txt` retains the three passing suite outputs. `FREEZE.json` binds
the source closure and current main commit. The v39 trace at
`results/map01-v39-coast-liveness-live-01` and the older v13 measurement
allocation remain unchanged.

## Environment

The construction suites ran on macOS arm64 with Python 3.14.5. No container
was started: the shared OrbStack inventory had no running containers but did
have four `Created` entries with unknown ownership, and the read-only image
listing returned a content-store error. Those entries were left untouched. This component-only
result does not claim container validation.
