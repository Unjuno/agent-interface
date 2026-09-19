# Grantor-side revocation versus pre-exec delegated capability — retained result

Task `COORD-GRANTOR-CAP-REVOCATION-20260917-026`, Issue #620. Publication BASE `46cbcadabdfe8685f52353f455264568ebf3b2e7`.

## Allocation history

A1 (`grantor-cap-revocation-20260917-a1`) hit the outer 45-second supervision ceiling because all six already-frozen chunks were mistakenly invoked inside one outer shell call. `m01..m06` completed; `m07` created DB/socket setup state but no result; `m08..m12` never started. A1 was not resumed, no consumed ID was rerun, and **zero A1 rows are pooled into the scientific result**.

A2 changes supervision only: fresh `n01..n12`, identical scientific sources/arms/scenarios/auditor, with each two-case chunk invoked by a separate outer tool call.

## Decision

**`PASS_GRANTOR_REVOCATION_SCOPED`.**

A2 has 12/12 fresh first outcomes, zero measured-ID reruns, and frozen-audit errors 0.

- Helper→task PID stays identical across exec: 12/12.
- The helper deliberately duplicates the capability to an inheritable alias before exec: the alias fd exists after exec in 12/12.
- `recipient_only/stable`: 3/3 alias usable; SCM_RIGHTS DB fd transferred; token `{A}`; generation2 commits.
- `recipient_only/B_change`: 3/3 alias usable; B omitted from token; B changes rev1→rev2; stale generation2 commits. This is the intentional unsafe negative control.
- `grantor_revoke/stable`: 3/3 alias fd still exists but is unusable after the grantor closes the server endpoint before ACK; task falls back to owner A/B receipts; generation2 commits.
- `grantor_revoke/B_change`: 3/3 alias exists but unusable; token `{A,B}`; B mismatch is detected; generation remains1 and no generation event is written.

Four copied-evidence corruption controls are rejected 4/4.

## Interpretation

Recipient-side FD_CLOEXEC is not a revocation mechanism for capabilities the trusted code has already duplicated/delegated to another inheritable fd. Moving revocation authority to the grantor closes this scoped leak even though the delegated fd object remains present in the post-exec task: the grantor endpoint is gone, so the capability can no longer produce the authoritative DB descriptor.

This supports a more precise rule: capability lifetime should be controlled by the authority that can invalidate the grant, not only by the recipient's fd hygiene.

## Limits

The helper cooperatively reports `BOUNDARY` before exec. A malicious helper can use the capability before reporting or omit the lifecycle notice. This does not establish independent exec detection, seccomp/namespaces, pidfd/ptrace semantics, cryptographic principals, distributed revocation, crash/power-loss behavior, performance, or a production security boundary.
