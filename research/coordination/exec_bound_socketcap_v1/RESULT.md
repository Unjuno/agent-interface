# Exec-bound socket capability versus same-PID identity persistence — retained result

Task `COORD-EXEC-BOUND-SOCKETCAP-20260917-025`, Issue #608. Publication base `8210ddde82f4b01c5d00042afb45fd64e85cd1da`; source-first freeze HEAD `7a5a44cc3e45042b57f51d7053c12da975d1cc25`.

## Decision

**`PASS_EXEC_BOUND_CAPABILITY_SCOPED`.**

Twelve fresh formal first outcomes completed once each (3 reps × 2 arms × 2 scenarios), with zero measured-ID reruns. The trusted helper `exec`ed the task and retained the same PID in **12/12** cases.

- `persistent_cap/stable`: 3/3 capability survives exec, SCM_RIGHTS DB fd is delivered, token is `{A}`, generation2 commits.
- `persistent_cap/B_change`: 3/3 capability survives exec, B remains outside the token, B changes to rev2, and stale generation2 commits. This is the intentional unsafe negative control.
- `cloexec_cap/stable`: 3/3 capability is absent after exec, B is read through the owner receipt path, token is `{A,B}`, generation2 commits.
- `cloexec_cap/B_change`: 3/3 capability is absent, B rev1→rev2 is detected, generation remains1 and no generation event is written.

Frozen audit: PASS with zero errors. Four postformal copied-evidence corruptions are rejected 4/4.

## Interpretation

A raw PID can persist across an `exec` trust-boundary change. In this scoped fixture, an inherited capability can instead be given an explicit code-lifecycle boundary: marking the socket endpoint `FD_CLOEXEC` removes it at exec even though PID is unchanged, forcing effect-relevant reads back through the receipt-producing owner.

This does not make CLOEXEC a complete sandbox. A trusted helper can duplicate/transfer a capability before exec or intentionally preserve it. The result establishes only that capability lifetime can be narrower than process-PID lifetime and can close this deterministic same-PID exec transition.

## Limits

One Linux container, local AF_UNIX socketpair/SCM_RIGHTS, Python 3.13/SQLite, cooperative trusted helper. No PID reuse stress, pidfd, seccomp/namespaces, cryptographic principal, malicious helper, distributed concurrency, crash/power-loss, latency or production-security claim.
