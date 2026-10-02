# Per-key release-time observability — construction result

**Disposition: `NON_IDENTIFIABLE_FROM_RETAINED_RELEASE_TELEMETRY`.** This is a
bounded event-timestamp construction against retained data. It is not a live
measurement or a scientific/runtime PASS.

## H / T / D / C / U

- **H:** Owner/event timestamps plus outer step completion may fail to identify
  the actual key-up time even when the requested hold duration is known.
- **T:** Against hash-pinned v39 `cover-1`, step 0 (`d`, declared 350 ms), the
  analyzer checked the `keys_held` acknowledgement at 55511911802240 ns and
  outer completion at 55512477276903 ns. Four construction/mutation tests
  passed before freeze; the frozen source-identity-checking analyzer ran once.
- **D:** Two different hypothetical key-up times fit those explicit
  timestamps: +350 ms (55512261802240 ns) and +500 ms (55512411802240 ns).
  Both are before step completion; they differ by 150 ms. No per-key key-up
  transition receipt exists for this selected step in the retained event
  stream. The analyzer returned the frozen non-identifiability disposition
  with zero errors.
- **C:** `step_completed` is an outer event boundary, not a physical transition
  sample. This construction establishes ambiguity in the explicit event-time
  telemetry, not invariance of the entire pixel/game trajectory under either
  counterfactual. Frames could indirectly constrain timing, but no calibrated
  independent mapping from frame effects to key-up is available here.
- **U:** Actual physical key-up, full held-input occupancy, causal effect,
  safety, useful-feedback onset, end-to-end latency and MAP01 completion remain
  unmeasured. The owner-thread explicit key-up timestamp experiment in #5156
  is still required and its A07 allocation remains STOP pending resource
  ownership resolution.

## Reproduction and provenance

Base main: `bcac9f7e5f7c49c44cd451a5331a510903097a9b`. Source hashes for both
retained event streams and hashes for the plan/analyzer/tests are in
`FREEZE.json`. The analyzer output is `RESULT.json`; package checksums are in
`SHA256SUMS`.

Before freeze: `python3 -m unittest -v test_analyze.py` passed 4 tests;
`python3 -m py_compile analyze.py test_analyze.py` and `git diff --check`
passed. After freeze: `python3 analyze.py` executed once and returned
`NON_IDENTIFIABLE_FROM_RETAINED_RELEASE_TELEMETRY`, errors `[]`. No container,
Xvfb, runtime, model, game or input was invoked.
