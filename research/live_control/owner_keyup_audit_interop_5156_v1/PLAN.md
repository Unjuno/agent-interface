# Allocation 05 — owner-v1 / completeness-v2 audit join

## H — hypothesis

An additive host-only join can reconcile owner-v1 release rows with explicit
v3 caller receipts and a separately frozen expected-release inventory, assign
the inventory's release IDs one-to-one, and then pass the normalized rows to
the unchanged v2 completeness auditor. Ambiguous, missing, duplicate, or
misordered evidence must fail closed. Autonomous cleanup is classified from
its expected trigger/reason/key identity and is not falsely given an explicit
caller envelope.

## T — bounded construction experiment

At main `6af2b750e37979de585d5a2e3c3d8e0c26926359`, pin PR #5298 head
`75082c44cfe5a829dc94ed3dc6341e149ff4e950` and PR #5415 head
`2b01248ff319a70ca7ddb19131f2f6cc4d7a2360`. Use source-shaped JSON fixtures
for two same-key explicit releases and one two-key-cleanup member; pair the
explicit v1 rows to caller-v3 receipts by owner, intent, key, and nested
monotonic interval. Assign expected IDs by frozen per-identity sequence only
after one-to-one matching. Run the unchanged v2 auditor over the joined rows.
Mutation controls cover empty/all omitted, one omitted, duplicate, wrong
identity, absent/duplicate/overlapping receipt, inverted caller and owner
times, invalid authority flags, and ambiguous expected sequence.

This is a source-contract/synthetic-construction rung, not an execution of
InputOwner or an X11 fixture. Docker/OrbStack is excluded because the current
#5085 shared-resource gate requires a fresh exact named allocation; this pure
data-join check needs no OS service and will run with the local Python runtime.

## D — decision gate

`PASS_JOIN_CONSTRUCTION_SYNTHETIC_ONLY` requires the valid repeated-key fixture
to produce exactly the frozen inventory and pass the pinned v2 auditor; all
frozen mutations must be rejected; and neither authority nor physical-key-up
claims may be introduced. Any missing, duplicate, ambiguous, identity-mismatched
or improperly nested evidence is `STOP`, not a scientific failure. The direct
v1-to-v2 incompatibility already observed in the exploratory check remains
preserved in issue comment #5910424260; this allocation freezes and tests a
distinct join construction rather than rewriting that record.

## C / U — limits

Fixtures are synthetic and source-shaped. No owner runtime, X server, Docker,
GUI/input, MAP01, model, or GPU is exercised. A pass validates only the adapter
contract and auditor composition; it does not establish actual event capture,
physical occupancy, application consumption, task effect, recovery, or live
completeness. The separate exact X11 allocation gate and future real-trace
admission/terminal binding remain open.
