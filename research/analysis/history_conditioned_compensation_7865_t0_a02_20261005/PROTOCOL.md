# Issue #7865 — T0 finite compensation-history experiment (A01)

Status: preregistration for a deterministic method-only test. No GUI, model,
network, live document, user data, or external write is used.

## H / T / D / C / U

**H.** In the frozen two-field artifact model, field-scoped compare-and-
compensate preserves an independent disjoint-field update and accepts that
recovery where a whole-object version guard aborts; it refuses same-field,
ABA, replaced-object, unknown-history, and out-of-order histories. A blind
whole-object inverse loses at least one planted independent update.

**T.** Enumerate six deterministic event histories against four policies:
`BLIND_INVERSE`, `WHOLE_OBJECT_VERSION_GUARD`,
`FIELD_SCOPED_COMPARE_AND_COMPENSATE`, and `NO_AUTO_COMPENSATION`. The
histories are no interleaving, disjoint-field write, same-field write,
write-away/write-back ABA, target replacement, and unavailable history. Add
one out-of-order receipt trace. Candidate replay and a separate oracle must
agree on final identity/generation/fields, preservation of external writes,
restoration of the agent-owned field, and disposition. No randomized seeds or
post-hoc fixture changes.

**D.** `PASS_METHOD_SCOPED` iff all candidate outputs exactly match the
independent oracle; blind inverse demonstrably erases the disjoint write;
field-scoped recovery preserves the disjoint write and refuses every
conflicting or unidentifiable history; no policy reports literal rollback
when it performed a compensating write. A deliberately corrupted field
revision and a deliberately corrupted footprint must be rejected by the
oracle check. Any mismatch is `FAIL_METHOD`; inability to distinguish a
history is `HOLD_UNIDENTIFIABLE`.

**C.** Whole-object version guard and no-auto-compensation may be safer and
simpler if field-level acceptance is not worth added contract complexity.
Even a correct field merge can violate cross-field application invariants.

**U.** The fixture assumes complete, ordered, versioned writes and independent
fields except where the trace explicitly removes that knowledge. Synthetic
success does not establish GUI undo reliability, real version availability,
semantic independence, task benefit, or safety.

## Frozen mechanics

Initial artifact: stable identity `doc-A`, generation 0, `{title: A, body: x}`.
The interrupted agent effect changes only `title: A -> B`, producing
generation 1 and title-field revision 1. Its recovery record binds the target
identity, base snapshot, effect footprint `{title}`, expected post-effect
value `B`, and expected title revision 1. External `body` or `title` writes
advance both object generation and that field's revision; replacement changes
identity; missing or non-monotonic receipt history makes order unknown.

The candidate's field-scoped policy may compensate only if history is known
and monotonic, identity is still `doc-A`, and both title value and revision
still equal the agent's recorded post-effect value/revision. Its compensating
write changes only title back to `A`, advances generation/revision, and is
reported as `COMPENSATED_NEW_EFFECT`, never `ROLLED_BACK`. The object guard
requires unchanged identity and generation 1, then restores the entire base
snapshot. Blind inverse restores the base snapshot without guards. The
no-auto policy always returns `CONFLICT_OR_HOLD` without writing.

The independent oracle is a declarative table derived from each named trace;
it must not import candidate functions. The exact source tree and container
image are hashed before the first candidate/oracle test. One standard-library
container execution is the formal T0 run; any source change after freeze
requires a new version and is not a repair of A01.
