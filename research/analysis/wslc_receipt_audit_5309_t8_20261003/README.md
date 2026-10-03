# T8 — Offline audit of the retained WSLc receipt

**Status before the one formal CLI validation:** `FROZEN_PRE_VALIDATION`. Candidate invocations: 0. WSLc invocations: 0. Docker invocations: 0. Retained-receipt CLI validations: 0/1. Retries: 0.

This is an offline successor to the formal `STOP_HOST_RECEIPT_SCHEMA_MISMATCH` on [Issue #6975](https://github.com/Unjuno/agent-interface/issues/6975), retained in [PR #6983](https://github.com/Unjuno/agent-interface/pull/6983). It validates only the exact captured T7 stdout; it does not launch WSLc, rerun the auditor, or revise T7's STOP.

## H / T / D / C / U

- **H:** The 306-byte stdout captured during T7 exactly matches SHA-256 `604fc18e94e80f6aa941623b8854ffad88043e16e5058db89aa45449ba97489f` and encodes the already-frozen 432-row finite-oracle receipt. The unchanged T6 auditor spells its yield-fallback result as `failed_probe_yield_wrong_target`; the T7 frozen host verifier expected the nonexistent alias `failed_probe_yield_fallback_wrong_target`.
- **T:** Input snapshot: `inputs/audit.stdout.json`, byte-identical to the output in PR #6983. Use only the standard-library validator and mutation tests in this directory. Expected values are recorded in `FREEZE.json` and were already fixed in #6975. The one formal CLI command and exact Python version are frozen there.
- **D:** `PASS_RETAINED_RECEIPT_SCHEMA_AUDIT` only if the exact input hash, exact key set/types, all counts and semantic identity match; the formal CLI emits the pass record; mutation tests reject byte/schema/value changes; and earlier STOP/raw/auditor files stay untouched.
- **C:** Post-hoc offline validation of retained output only. It is a separate allocation and cannot convert T7's frozen STOP to PASS because T7 required its own frozen host verifier to pass.
- **U:** No WSLc/Docker/native-WSL invocation, no candidate, no performance or memory/OOM claim, no GUI/model/application effect, and no edit to T6 or #5309 history.

## Protocol

The eight mutation tests passed before the formal CLI validation. After the preregistration files are present on the draft PR, run `python -B verify_receipt.py inputs/audit.stdout.json` exactly once. Preserve stdout, stderr and exit status under `stage-output/`; do not retry, even if the validator fails.

The new validator uses the actual immutable auditor schema. The original T7 verifier and its failing run remain unchanged in the predecessor evidence package.

