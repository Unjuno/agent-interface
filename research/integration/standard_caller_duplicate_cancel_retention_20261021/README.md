# Standard caller duplicate-cancel retention characterization

## Question

The independent safety-owner duplicate-cancel experiment is already closed as
`PASS_DUPLICATE_CANCEL_IDEMPOTENCE_SCOPED` in [Issue #814](https://github.com/Unjuno/agent-interface/issues/814): repeated same-token delivery produced one release. The public standard-caller composition has a different seam. Does it return a stable cancellation-operation receipt to the duplicate caller and retain cancellation evidence separately from the original action result?

## Frozen execution

One local Fake X trial was run through `create_server` and the public
`interface_guarded_input`, `interface_guarded_cancel`, and `interface_results`
tools at source revision `e892485a003a2cce62bb6ee6c4ee5bf29949b058`. No WSL/WSLc,
Docker, real X server, physical input, model, or provider was used. The owner
emitted a synthetic `CTRL` press and then blocked in Fake X sync. The standard
caller received two sequential cancel requests with the same call ID. The
disconnect and release-worker receipts were controlled fixtures, not live
platform observations. Conditions and the complete private raw result remain
under this directory's `conditions.json` and `raw/`; the sanitized copy is in
`public-evidence/`.

Verify the private raw characterization with the root packet `audit_raw.py`,
passing its private raw, public-copy, audit-output, and source-revision
arguments. The exact `r02` receipt SHA-256 is recorded in the public audit.
Verify the committed sanitized copy from its directory with `python -B
audit_raw.py`; `SHA256SUMS` binds every public packet file.

The first invocation attempt `r01` stopped before server construction because
the script launcher omitted the repository root from `PYTHONPATH`. Its
traceback is preserved and it was not retried. `r02` used a fresh run identity
and changed only the launcher environment.

`python --version` in the workspace immediately after `r02` reported 3.11.9;
the interpreter identity was not embedded inside the raw trial receipt, so this
is recorded as an environment observation rather than an in-receipt field.

## Result

`r02` made exactly one release-helper call. The first standard-caller cancel
returned `cancel_requested`, with cleanup `UNKNOWN`, `release_confirmed=false`,
`task_success=null`, and replay denied. The same-call duplicate returned
`not_active`, not the same operation receipt; neither response carried a
cancellation-operation ID. `interface_results` eventually returned the
original action as `runtime_failed`, still `UNKNOWN`, with null task success and
replay denied. It contained no separate cancellation subrecord. Its saved
owner-process liveness snapshot said `alive=true`/`retired=false`, while the
cancel response recorded owner retirement and exit code `-15`; this is stale
action-result metadata, not evidence the process survived.

The 16 ms first-cancel interval is one controlled Fake X observation, not a
bounded-response estimate. The release helper's synthetic `verified` receipt
was not promoted: the caller kept release unknown because a late server request
remained possible. This preserves the distinction between one cleanup attempt
and a physically confirmed, safe release.

## Disposition

This does not repeat Issue #814's independent-owner semantic trial. It shows
that same-call duplication reaches only one cleanup attempt in this controlled
standard-caller path, while operation identity and result retention are not
integrated. The proposal in
[`docs/architecture/PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md`](../../../docs/architecture/PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md)
therefore needs a bounded per-call cancellation-operation registry and a
separate retained result that remains additive to the original action report.
The observation is one Fake X baseline, not an implementation pass, live-X
release claim, task effect, MAP01, or efficiency result. Preserve this outcome;
the next useful test is the same public composition against a prototype
registry/supervisor under delayed cleanup, with duplicate callers observing one
operation ID and one release attempt.
