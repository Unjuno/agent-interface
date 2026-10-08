# Issue #6210 — schema-equivalence T0

Allocation: `SCHEMA-EQUIVALENCE-6210-T0-20261002-01`  
Source base: `2a01df459a488f1e09d20c57afc09ddc683420fd`  
Disposition: **STOP before formal candidate**; see `STOP.md`.

## H / T / D / C / U

- **H:** For at least one preregistered same-model desktop task family, two
  independently certified equivalent tool surfaces may yield materially
  different proposals, abstention, exact-effect success, or model cost. This
  T0 does not test that hypothesis.
- **T:** Exhaustively enumerate the authored 2×2×2 finite fixture (target
  authorized/wrong × observation current/stale × completion/cancel-after-type)
  over eight tool surfaces. Compare input mapping, primitive action trace,
  model-visible call-boundary profile, authority, intermediate release
  checkpoint, and terminal state. The independent auditor reconstructs rows
  without importing the candidate and checks four planted corruptions.
- **D:** A method pass would require all 64 rows to match the independent
  oracle, exactly `canonical` and `renamed_fields` to be certified equivalent,
  and all four corruption controls to be rejected. The formal candidate and
  auditor were not invoked, so there is no T0 result.
- **C:** Split/merge call boundaries expose different opportunities for model
  intervention and therefore are conservatively non-equivalent at the
  model-visible interface, even when flattened primitives or final effects
  match. The finite cancellation fixture covers cancellation after typing,
  not every possible interruption instant.
- **U:** Synthetic, hand-authored semantics only. No model, tool server, GUI,
  OS input, application effect, latency, token cost, or product benefit was
  tested. No action authority is granted.

## Construction checks (not formal allocation evidence)

On host CPython 3.14.5 / macOS, `python3 -m unittest -v test_equivalence.py`
passed 5/5 and `python3 -m py_compile candidate.py audit.py run_candidate.py`
passed. An earlier intentionally naïve classifier failed the negative-control
test (3 passed, 1 failed); it was corrected before this freeze. These are
construction checks only and are excluded from the formal T0 denominator.

## Runtime boundary

`wslc`/`wslc.exe` is unavailable in this macOS environment. Docker exists, but
the frozen T0 is a pure finite CPU transition-oracle test and does not require
Engine API, Compose, unsupported isolation/resource controls, or GUI behavior;
the governing protocol therefore does not authorize substituting Docker. The
formal invocation stopped before candidate start: candidate=0, auditor=0,
container=0. No shared engine or allocation was touched. This is a runtime
availability STOP, not a scientific FAIL or PASS.

Exact frozen identities and hashes: `FREEZE.json`. No candidate output is
present or implied.
