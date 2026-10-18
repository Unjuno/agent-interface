# Issue #8112 A02 construction log

- Predecessor A01 stopped at the exact-main gate with candidate/auditor 0/0 and
  no formal retry. A02 has a separate path and allocation identifier.
- The A09 pinned Python image (`dddfd7...e0016`) was not present locally.
  The previously cached Python 3.14.8 Linux/arm64 digest
  `c3e521...ce40151` was inspected and selected; no image pull was attempted.
- The A09 `FREEZE.json` / `SHA256SUMS.txt` candidate and auditor hashes do not
  match the current-main source bytes at the A09 paths. A02 preserves that
  provenance discrepancy and freshly freezes the actual current-main bytes
  (candidate `caf4a7...0465`, auditor `7ed3a6...1e3d`) before any formal call;
  it does not claim those bytes match the A09 historical freeze.
- A read-only candidate-source bind preflight on that image passed in OrbStack
  (source bytes 2,836); candidate/auditor invocations 0/0. `PREFLIGHT.json`
  retains command, output, and source hash.
- Local protocol tests exercise exact 36/24/12 counts, candidate/truth
  separation, A09 source-byte identity, and mount syntax. They are construction
  checks, not evidence about TTC-vs-simple-cue performance.
- Formal execution remains 0/0 until `FROZEN.json` is written, latest-main
  identity rechecked, and the exact one-shot runner invoked.
