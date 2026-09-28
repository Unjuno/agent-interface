# Successor #5219 — strict audit of temporal receipt evidence

Allocation: `kernel-receipt-time-5215-audit-successor-20260929-01`  
Frozen main: `d8ca8bfed9cd8d84201c91645e4ed25364181d3f`  
Branch: `research/kernel-receipt-time-5215-audit-successor-20260929`  
Evidence path: `research/analysis/kernel_receipt_time_5215_audit_successor_20260929/`

## H / T / D / C / U

**H.** The retained #5215 outcome audit is not fail-closed: missing, null, or
mistyped temporal-negative fields can yield `NO_GAP_OBSERVED`. The stored record
also omits the PLAN's effect-at-900 baseline, and exact effect-at-execution-end
semantics are internally contradictory. A strict independent oracle should
HOLD incomplete evidence and surface the ambiguity.

**T.** Freeze current-main identities for the retained #5215 PLAN, probe output,
legacy audit output/source, and #5219 intake result/check. Reproduce the
historical audit from its immutable input, then run a separate stdlib-only
oracle against the same copied record. Exercise the unmodified record; remove,
null, string, and integer-mutate each required boolean independently; test an
unmanifested effect-at-900 addition; and evaluate both stated interpretations
of the effect-at-end boundary. No kernel/probe rerun, runtime change, Docker,
GPU, model, GUI/input, provider, or external service.

**D.** `PASS_AUDITOR_GAP_SCOPED` if the legacy audit reproduces its stored
outcome, all malformed/incomplete copies HOLD under the strict oracle, and the
original record HOLDs for its missing case and boundary contradiction.
`NO_AUDITOR_GAP_OBSERVED` only if the required evidence is complete, malformed
copies HOLD, and the boundary contract is unambiguous. Identity mismatch or
oracle disagreement is `HOLD_SOURCE_OR_ORACLE`. This is an evidence-adjudication
result, not a kernel/runtime behavior result.

**C.** Exact original bytes and source pins are fixed; mutations change one
field at a time. The independent oracle is stdlib-only and imports neither the
kernel, original probe, nor the legacy audit implementation. A complete
synthetic schema control tests type/missing-field handling only; it cannot
upgrade the original record or resolve contract meaning.

**U.** One Windows host and the retained kernel-v1 evidence only. No new
runtime/GUI/model execution, OS lease guarantee, backend clock comparability,
real input effect, production correctness, or performance claim. Even a strict
audit PASS does not authorize runtime adoption; clock/lifecycle compatibility
remains open.

## Frozen evidence identities

Exact Git blob IDs and SHA-256 values for all consumed main evidence are in
`FREEZE.json`. The source commit is pinned to current `main` at intake. The
historical PLAN and probe are retained unchanged under
`runtime/results/kernel-time-intake-01/`.

## Run

From repository root:

```powershell
python -m unittest discover -s research/analysis/kernel_receipt_time_5215_audit_successor_20260929 -p 'test_*.py' -v
python research/analysis/kernel_receipt_time_5215_audit_successor_20260929/run_audit.py
```

The runner writes one immutable `evidence/` capture and refuses to overwrite an
existing capture. It verifies all frozen Git blobs and content hashes before
reading the original record.
