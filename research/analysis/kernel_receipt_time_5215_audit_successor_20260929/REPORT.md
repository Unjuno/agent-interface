# Issue #5225 — temporal-receipt audit evidence integrity

Disposition: **`PASS_AUDITOR_GAP_SCOPED`**. This is an independent audit of
the retained #5215/#5219 records. It is not a rerun of the kernel experiment,
not a runtime defect result, and not authorization to adopt a kernel change.

## H / T / D / C / U

The frozen plan and source identities are in [`PLAN.md`](PLAN.md) and
[`FREEZE.json`](FREEZE.json). The independent stdlib oracle is
[`audit.py`](audit.py), the immutable copied-data outcome is
[`evidence/audit-matrix.json`](evidence/audit-matrix.json), and the separate
result checker is [`verify_capture.py`](verify_capture.py).

## Executed result

The saved #5215 legacy audit was executed against its retained
`probe-output.json` and reproduced byte-semantically exactly the committed
`audit-output.json`: `PASS_TEMPORAL_RECEIPT_GAP_SCOPED`, four invalid temporal
cases accepted, zero legacy audit errors. No kernel or scientific probe was
run.

The pinned #5219 intake record independently preserves three copied controls
(all four temporal-negative flags removed, null, or strings); the old audit
classifies each as `NO_GAP_OBSERVED` with no errors. Our strict oracle does not
promote that result:

- The original probe output omits `effect_at_900`, although the frozen plan
  names it as a baseline acceptance case. Original record → `HOLD_SCHEMA`.
- At `effect_at_700`, the plan says “reject at execution end” but also labels
  that instant “causally eligible”; the legacy auditor requires `true`. The
  strict oracle refuses to choose an interpretation. A complete, correctly
  typed schema-only control → `HOLD_CONTRACT_AMBIGUITY`.
- Mutating each of the ten required boolean keys independently to missing,
  null, string, and integer produced **40/40 `HOLD_SCHEMA`** decisions.
- Adding an `effect_at_900` boolean to the old record without adding frozen
  source provenance still returns `HOLD_SCHEMA`; a copied value cannot create
  a missing observation.

The second, independent capture checker passed all 11 invariants and rechecked
all six current-main Git blob IDs plus exact file SHA-256s. Retained matrix
SHA-256: `a7f50a716b48313f2214da3cd097f1674225dc03ddbec74fefc81324453cb700`.
The strict result is a new evidence-integrity finding only. The original #5215
PASS and #5219 `HOLD_RUNTIME_ADOPTION` are not edited or relabeled.

## Verification and execution limits

Commands, from the frozen main checkout:

```powershell
python -m unittest discover -s research/analysis/kernel_receipt_time_5215_audit_successor_20260929 -p 'test_*.py' -v
python research/analysis/kernel_receipt_time_5215_audit_successor_20260929/run_audit.py
python research/analysis/kernel_receipt_time_5215_audit_successor_20260929/verify_capture.py
```

Observed results: 5/5 unit tests; `PASS_AUDITOR_GAP_SCOPED`; legacy audit
reproduced; 40/40 mutations held; independent capture check `passed=true`.
Source/kernel files were unchanged. No Docker was used because #5215/#5225
explicitly specifies CPU-only host execution and prohibits Docker for this
question. No GPU, model, GUI/input, provider, network experiment, or workflow
result was used.

After preserving the first matrix, one accidental repeat of the immutable
runner was attempted while rechecking the capture. It stopped at the
pre-existing `evidence/` directory with `FileExistsError` before rewriting any
file. The independent capture verifier then passed against the preserved first
matrix. This is the runner's intended no-overwrite guard, not a second result.

The first verifier pass caught that its own source hash in the manifest had
been measured before a small verifier edit; that manifest pin was refreshed,
and the final verifier pass checks every study-source digest. One hash lookup
also used the task-parent directory rather than the Git worktree and returned
a path-not-found error; it was repeated in the worktree with no file changes.

An initial inspection command was run from the task parent instead of the Git
worktree and therefore found no repository paths; it made no changes and ran no
tests. All frozen-source reads and experiment commands above were rerun from
the actual worktree. A separate PowerShell hash command also first hit a
brace-expansion parser error; it was corrected before the source identities
were frozen or the audit matrix was generated.

## Limits / next gate

One retained evidence bundle and one host only. This does not establish whether
the old kernel accepts new cases, whether backend and kernel clocks are
comparable, how late receipts should be handled, or whether public execution
enforces lease deadlines. Resolve exact equality semantics, produce the missing
baseline observation from a separately authorized source if available, and
specify clock/lifecycle boundaries before any runtime-adoption allocation.
