# Issue #6536 T0 — claim-scoped clip-to-trace method discriminator

This additive package tests a synthetic, finite provenance contract. It does not read, edit, or publish any retained video or trace. The exact hypothesis, decision gates, case definitions, and one-shot procedure are frozen in `FREEZE.json` and `REPORT.md` before the candidate run.

## H / T / D / C / U

- **H:** A claim-scoped map plus independent raw-only audit rejects planted clip-as-whole-run, clock, source-identity, outcome, and control-attribution errors while accepting honest excerpt claims.
- **T:** Run the frozen eight-case synthetic fixture through evidence arms A (clip + caption), B (clip + master link), C (hashed EDL only), and D (claim-scoped map + independent auditor). Candidate and auditor are separately implemented; the auditor consumes only fixture and raw candidate output. Run mutation controls after the first raw audit.
- **D:** `METHOD_PASS_SCOPED` requires D to accept both honest excerpt claims, reject all six unsupported broad/forged claims, reconstruct every arm decision, and reject every frozen mutation. Any false D acceptance/rejection or baseline/raw mismatch is `FAIL_METHOD`; missing identities or incomplete output is `STOP`.
- **C:** Human reviewers may already infer scope correctly from a full master and trace; the synthetic model may underrepresent real media/transcoding and clock complexity. A hash/signature establishes byte identity, not truthful capture or task success.
- **U:** Synthetic timestamps, frames, and scorer receipts only. No real video, C2PA signing/validation, GUI/game/model, controller, task outcome, human review, public claim, or product/safety conclusion.

## Reproduction

From the repository root:

```sh
python3 research/analysis/claim_scoped_clip_trace_6536_t0_20261002/candidate.py
python3 research/analysis/claim_scoped_clip_trace_6536_t0_20261002/audit.py
python3 -B -m unittest discover -s research/analysis/claim_scoped_clip_trace_6536_t0_20261002 -p 'test_*.py' -v
```

`fixtures.json` and source hashes in `FREEZE.json` bind the frozen inputs and source. `RAW.json` is the retained first candidate output; `AUDIT.json` is the retained independent audit. `SHA256SUMS` covers the retained package files.

The frozen result is `PASS_METHOD_SCOPED`; see `REPORT.md` for the observed false-acceptance counts and limits.
