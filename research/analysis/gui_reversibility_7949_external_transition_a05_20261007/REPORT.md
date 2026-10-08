# Issue #7949 A05 — event-observed transition recovery certificate

**Disposition: `PASS_EXTERNAL_TRANSITION_SCOPE`.** This is a finite authored
model result only; it is not a GUI, application, safety, or runtime result.

## Hypothesis and decision

After a complete external write changes state `100→101` and revision `1→2`, a
recovery certificate bound to revision 1 must become UNKNOWN. After replaying
the complete event and binding a fresh certificate to revision 2, bounded
recovery can clear the agent-owned bit and reach `001` while preserving the
external bits. A gapped event chain must remain UNKNOWN.

The frozen decision required all three cases to match, no lost external bit,
no recovery under a stale certificate or invalid journal, and zero independent
audit errors. The candidate and auditor each ran once; no retries.

## Formal outcome

- `pre_interference`: `UNIVERSALLY_UNIFORM`, `100→000` via `restore_a`.
- `stale_then_refreshed`: rev-1 certificate after the rev-2 event is
  `UNKNOWN_STALE_CERTIFICATE`; a fresh rev-2 certificate is
  `UNIVERSALLY_UNIFORM`, `101→001` via `clear_owned_a`.
- `journal_gap`: `UNKNOWN_EVENT_CHAIN`, with no recovery emitted.
- Candidate: one invocation, tool-reported exit 0.
- Independent raw-only auditor: one invocation, tool-reported exit 0;
  disposition `PASS_EXTERNAL_TRANSITION_SCOPE`, three cases, zero errors.
- Preformal auditor-core validation: 3/3 tests pass, including acceptance of a
  correct gapped-history UNKNOWN and rejection of three hostile mutations.

## Provenance and limits

Base commit: `9fb2dd6782d1d1477a00d14be870487fd4c54fa2`. Run ID:
`gui-reversibility-7949-external-transition-a05-20261007`. Native macOS
CPython 3.14.5, standard library only; no container-isolation claim. OrbStack
read-only image inventory previously failed with containerd
`operation not supported`; no container/VM state was changed. A01/PR #7971,
and A02/A03/A04 records are unchanged.

Raw candidate SHA-256:
`e0472769b92b4fa0b8f41e31ec23b5bdd2d2d8485c21f29a08e785d10b6e497f`.
Auditor JSON SHA-256:
`a15abb5dd9fe7b65577fa13fd01eb818c86305af278d699f4e61f5233908d4cf`.
Frozen source/input hashes and exact commands are recorded in `FREEZE.json`;
candidate/audit outputs are under `results/`.

This establishes only behavior in three explicitly authored 3-bit cases with
complete supplied event provenance and recovery horizon 1. It does not show
that any real application exposes a complete journal, that a real receipt is
authentic, that recovery semantically restores an application, or that a GUI
action is safe or authorized. No runtime/admission behavior is proposed.
