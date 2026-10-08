# Issue #5730 — retained construction result

## Decision

`FAIL_CONSTRUCTION_CLEANUP_GAP`. The one-shot synthetic matrix correctly refused scientific evaluation and emitted no raw scientific hash for an output whose post-write digest changed. However, the tampered bytes remained observable at the output path after the gate returned STOP. A consumer that reads the path without respecting the typed status could mistake those bytes for a published artifact. The hypothesis that malformed or changed output is fully prevented from publication is not supported.

The original `RUN.json`, `EXECUTION.json`, `FREEZE.json`, stdout/stderr bytes, and first independent `AUDIT.json` are retained unchanged. The v1 audit's `FAIL` is preserved. `audit_v2.py` is an additive interpretation correction: it distinguishes the tampered postwrite output-path residue from a scientific raw hash, while still concluding `FAIL_CONSTRUCTION_CLEANUP_GAP`. The candidate matrix was not retried or rerun.

## H / T / D / C / U

- **H:** Not supported as stated: 10 of 11 cases met their expected decision, but post-write corruption left file residue after STOP.
- **T:** One CPU-only host run on CPython 3.11.9, frozen main `5ff239141f49c1603c0f6b078268f4a2f6e082df`; 11 synthetic cases. Candidate callbacks: 5 total; prerequisite failures: 6 with zero callback. No GPU/CUDA, Docker, model, game, GUI or input.
- **D:** `FAIL_CONSTRUCTION_CLEANUP_GAP`. Independent v2 raw auditor: 11/11 case decisions and invocation counts reconstructed, frozen source hashes match, four auditor mutation controls pass. The postwrite tamper case returned `STOP_POSTWRITE_DIGEST_MISMATCH`, `NOT_EVALUATED`, and null `raw_sha256`, but the transient output path still contained bytes when inspected.
- **C:** Host Python callback, synthetic process-result objects, temporary filesystem and a controlled `os.replace` tamper hook. No production launcher or Windows durability guarantee tested.
- **U:** No evidence about GPU inventory correctness, resource exclusivity, CUDA arithmetic or performance. A safe successor would need a distinct frozen allocation and should write to a private staging path, validate bytes before publication, and remove/quarantine any destination on mismatch. This report does not implement or test that successor.

## Exact retained execution

- Candidate command: `python -B run_construction.py` — exit 0; 11 cases, 5 synthetic callback invocations.
- First separate audit: `python -B audit.py` — exit 1, `FAIL`, only error `postwrite_digest_mismatch: invalid output published`.
- Additive separate audit: `python -B audit_v2.py` — expected scientific decision is a failure, exit 1: `FAIL_CONSTRUCTION_CLEANUP_GAP`, integrity errors empty.
- Gate tests before the frozen matrix: `python -B -m unittest -v test_gate.py` — 11/11 pass. This was preflight, not a second candidate allocation.
- No candidate retry occurred.
