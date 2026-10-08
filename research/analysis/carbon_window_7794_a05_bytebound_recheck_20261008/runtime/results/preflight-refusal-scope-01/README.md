# Explicit scope on X11 preflight refusals

The primary Calc trial in public-review-live-01 returned a BACKEND_CONSTRAINT
before program execution while backend_emissions was 16 from earlier input.
That cumulative counter made the current operation's effect boundary hard to read.
X11 preflight refusals now explicitly record program_execution_started=false,
program_emissions=0 and cleanup_attempted=true. The cumulative counter remains
unchanged. Cleanup can itself emit releases; this does not claim no physical input.
No admission, lease, focus, execution, release or replay behavior changes.

Both initial and repeated backend preflight refusal paths report this scope. The
public outcome summary copies strictly typed explicit fields. Historical receipts
without them remain without them; malformed values become null rather than false.
A control starts with 16 prior emissions and increments cleanup to 17 while execute
is never invoked. A disappearing-target control covers the repeated preflight.

Validation: 26 focused checks, 274 protocol checks and 126 harness checks pass.
This is construction validation of reporting, not a new GUI trial, matched
performance result, or evidence of human tempo. Frozen Calc evidence is unchanged.

The same intake also rechecked #5156's release receipt compatibility evidence.
Current-main owner/wrapper/protocol blobs match the frozen identities. The existing
raw-result auditor reproduces the six-of-seven compatibility failure set. Its PASS
means the failure was audited, not that the candidate passed. Keep
HOLD_RELEASE_RECEIPT_INTEROP; no owner timing candidate is promoted. This was only
a read-only re-audit, not a repeated probe or formal X11 run.

The archive retains local logs, intake/audit results and exact changed source.
Run python3 -O runtime/results/preflight-refusal-scope-01/verify.py for byte and
result verification. It does not execute archived code.
