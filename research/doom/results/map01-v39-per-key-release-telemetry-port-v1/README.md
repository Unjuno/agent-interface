# Current v39 per-key release telemetry port — construction corrected, native HOLD

This additive port brings per-key release transitions onto the backend selected
by the retained v39 source closure. `session_map01_v12.py` selects
`doom_typed_release_backend_v3.py`; the release owner is current `InputOwner
v10` wrapped by `input_transition_owner_v3`.

The first adapter candidate, frozen in `FREEZE.json`, buffered and flushed
receipts only within one `execute(step, ...)` call. Review reproduced a missing
receipt when the same held-key batch was released across successful executor
steps. That original source and its outputs remain unchanged as historical
evidence. The follow-up correction is in `SPLIT_STEP_FIX_01.md`: successful
steps of one program now share a release buffer until the held-key set is empty;
each receipt retains its own step number. Exceptions still discard buffered
partial measurements, and a different program identifier cannot inherit them.

## H / T / D / C / U

- **H:** Current v39 retains per-key explicit-up brackets for each executor
  program, including when its key releases span multiple successful steps, and
  takes one empty-owner sample before publishing that complete batch.
- **T:** Reproduce the split-step loss against the frozen candidate, preserve a
  multi-step regression, fix buffering without allowing partial exception
  receipts to verify, and run candidate, retained adapter and owner suites.
- **D — `PASS_CONSTRUCTION / HOLD_NATIVE_VALIDATION`:** 18 candidate tests,
  11 retained adapter tests, and 8 retained owner-wrapper tests pass (37 total).
  The new regression first failed on the frozen candidate with actual output
  containing only the final key (`space`), then passed with both keys in order,
  a single post-batch owner sample and per-receipt step numbers. Exception
  cleanup remains fail-closed. Python byte-compilation and `git diff --check`
  pass.
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
