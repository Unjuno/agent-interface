# Issue #3830 — short write and request-only crash characterization

Allocation: `issue3711-shortwrite-requestcrash-localdocker-formal01`
Frozen source commit: `3fa567baa277d1bfdfe415e522b419e6414d7c26`
Container image: local cached `python:3.12-slim-bookworm` (resolved image ID and immutable repo digest recorded in RESULT.json).
No runtime code is modified or mounted writable. Scope is synthetic characterization only.

## H / T / D / C / U

**H:** A short stdout write that returns a strict prefix can be distinguished from complete delivery, and request-only recovery after a child exits before report publication remains explicitly unknown/incomplete and non-replayable.

**T:** A source-frozen standalone runner uses only a private temporary directory and synthetic bytes. Case A persists request + exact JSON report, then a one-shot writer accepts a strict prefix and returns the prefix length without raising; the harness requires an explicit delivery-incomplete state while read-only recovery returns the original full report bytes. Case B launches a child that exclusively creates request.json, flushes/fsyncs it, then terminates with a preregistered exit code before report publication; recovery must yield `unknown_or_incomplete`, must not expose a completed result or replay operation, and backend invocation count remains one. A separate auditor recomputes each invariant directly from raw files without importing runner helpers.

**D:** `PASS_SYNTHETIC_SHORTWRITE_AND_UNKNOWN_RECOVERY` iff both cases satisfy all gates, each manifest hash matches, independent auditor returns zero errors, and corruption controls (altered recovered-report digest metadata, forged completed status, and forged full-delivery status) are rejected. Otherwise retain the exact FAIL/STOP/HOLD. One formal run, zero retries.

**C:** Local Windows + local network-disabled Docker; cached image only, read-only source and isolated result mount. No host GUI/input/model/provider, no GPU, packages, runtime edits, cleanup/prune, or prior evidence modification.

**U:** Exact synthetic file/process/stdout-writer contract only. No production CLI behavior claim, OS/network stdout generalization, power-loss claim, or GUI/backend effect.

## Execution

See `RUNBOOK.md` for exact one-shot commands and `RESULT.json` / `audit.json` for machine-readable outcome. `SHA256SUMS` binds only the frozen executable files and fixture bytes used by formal-01; documentation and post-formal corruption-control code are not formal inputs. These are retained records; do not rerun formal-01 in place.
