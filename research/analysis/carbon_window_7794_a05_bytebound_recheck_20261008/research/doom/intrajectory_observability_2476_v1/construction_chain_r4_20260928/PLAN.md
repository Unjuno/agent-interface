# Issue #2476 — evidence-complete cumulative-drift construction r4

Allocation: `issue2476-track-cumulative-drift-evidence-construction-r4-20260928`.
This is a new successor to the immutable r3 operator STOP, not a retry or relabel of r3. r3 remains `STOP_OPERATOR_INVOCATION_ERROR_NO_RETRY`; its missing-argument call consumed r3, and no command is repeated under that allocation.

## H / T / D / C / U

**H.** Explicitly recording literal `physical_input_emitted: false` on every scheduled row, including hops skipped after fail-closed stop, lets an independent raw auditor verify the bounded synthetic cumulative-drift construction without interpreting absence as no input.

**T.** Ten fixed synthetic trajectory shapes × two fixed policies × three scheduled hops (60 rows). Instrumentation/evidence completeness is the only treatment. Preserve the fixed 8 px local corridor, 12 px cumulative cap, score/margin, age, geometry and sequence limits. Runner emits every scheduled row; independently implemented auditor reconstructs decisions from frozen cases and rejects missing/true emission flags, missing rows and reordering. Run frozen auditor unit tests and CLI-option preflight before exactly one local construction invocation. No formal #2476 matcher/trajectory invocation.

**D.** `PASS_CUMULATIVE_DRIFT_EVIDENCE_CONSTRUCTION_ONLY` only if all 60 rows reconcile; exact and 12 px boundary cases continue 3/3; repeated +8 residual continues under per-hop-only but bounded policy stops at hop 2; 13 px chain stops at hop 3 under bounded policy; invalidation controls stop at expected steps; all emissions are literal false; independent audit has zero errors; and all four frozen corruption controls reject. Any mismatch is retained as typed FAIL/HOLD/STOP with no retry.

**C.** Local Docker `python:3.13.5-slim-bookworm`, pinned by image ID, linux/amd64, network none, read-only root/source, separate initially empty writable runner/audit directories, 1 CPU, 256 MiB memory/swap, 32 PIDs, all capabilities dropped, no-new-privileges. Correct CLI is frozen as `run.py --source /source --out /out`; auditor is a separate invocation reading `/runout/raw.json` read-only and writing `/auditout`. stdout/stderr/exit receipts stay outside both mounted result dirs. No GUI/game/X11/matcher/OS input/model/provider/training/Actions.

**U.** Synthetic state/evidence boundary only. No real visual tracking, task effect, physical input/release safety, 12 px optimality, or formal #2476 BASELINE/TRACKED/ABSTAIN result.

## Frozen invocation protocol and stop

The prior r3 operator error is the reason for the explicit argv/output-mount contract. A `--help`/option preflight must confirm `--source` and `--out` before the allocation invocation. Any unexpected nonempty output, image/source identity mismatch, Docker error, nonzero exit, missing artifact, auditor error, or failed control is retained as this r4 first outcome. Do not repair, retry, replace, tune, or relabel this allocation.
