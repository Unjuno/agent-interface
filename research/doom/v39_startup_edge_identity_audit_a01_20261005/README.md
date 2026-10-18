# V39 startup edge identity audit A01

This package independently audits the retained fake-X startup trace from
`map01_v39_startup_release_order_a01_20261005` PR #7881 A03. It joins each
`input_admission` row to one `input_release_transition` and the nested
`owner_explicit_keyup` receipt, checks the matched identity fields and time
boundaries, and independently checks the between-UP operation trace.

The audit is posthoc and uses no new runtime or live allocation. The
contextual identity-join subcheck can pass while the required instrumentation
gate remains `HOLD_EFFECT_LINK`: the retained fake-X data do not contain a
per-actuation ID, authoritative physical-occupancy sample, or independently
observed task-effect interval. XTest/XSync completion is not promoted to those
claims.

See `PLAN.md` for H/T/D/C/U, `FREEZE.json` for inputs and source identities,
and `results/AUDIT.json` for the independently reconstructed result.

The contextual identity-join subcheck passed: the two distinct-key admissions
join to exactly one release transition and owner-thread XTest/XSync receipt
each. The required instrumentation gate remains HOLD because the trace has no
independent task-effect interval per actuation.
The audit reconstructed the operation order with only one sync between the two
UPs and no `query_keymap` call. The observed software-call gaps from input
acknowledgement to release-call start were 142.500 µs (F8) and 29.200 µs
(SPACE); these are request-boundary differences, not physical hold durations.
Four mutation controls rejected a mismatched intent, duplicated release,
reversed receipt chronology, and wrong keycode.

Overall disposition remains HOLD: the trace has no actuation ID, authoritative
physical-occupancy sample, or independent application-effect interval. Its
contextual join only distinguishes the two different keys in this one trace;
it does not distinguish repeated same-key actions within one step.

The copied raw and candidate are from PR #7881 head
`e02617b0d806dd05dd0cb24e44dbb4db2d393bd4`, whose source base is
`b347d6f1ede81f6980932f2d7cba6d4758bf49c9`. The five current-main source
files pinned by this audit have the same newline-normalized digests at base
`c1074c4dc385bae5b94ce93a5870e92c2e6ab07d` as that retained source freeze.

Reproduce from the repository root:

```sh
python3 -B research/doom/v39_startup_edge_identity_audit_a01_20261005/audit.py
```
