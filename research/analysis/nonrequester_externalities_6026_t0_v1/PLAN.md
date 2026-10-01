# #6026 T0 preregistration and scope

## H/T/D/C/U

- H: On the frozen synthetic fixture, the fast route's requester-only completion time improves while synthetic non-requester active-effort burden is present; a complete affected-principal ledger exposes that inversion.
- T: Deterministic, standard-library-only accounting over seven offered task IDs, two routes, one requester and two collaborators. Include no-contact requester control, useful scheduled approval, redundant pings, a three-event alert burst, duplicate review, no-response, cleanup, and suppressed notice. Candidate emits route × principal vectors, event-status counts, and maximum burst count/minutes; an independently implemented auditor reconstructs these from raw fixture events. Six adversarial mutation classes cover recipient omission, delivery status, burst multiplicity, review minutes, nonresponse, and duplicate task×route assignment.
- D: PASS_METHOD_SCOPED only if every assignment/event/recipient is preserved, the requester contrast (14 synthetic minutes), route-specific collaborator vectors, and maximum bursts are independently reconstructed, useful/zero-contact controls remain distinct, and all mutations are rejected. Any missing assignment, recipient, event, or response state is FAIL_METHOD.
- C: In real use notifications may be silent, scheduled or beneficial; task effects might not transfer across routes. The synthetic fixture cannot estimate those.
- U: Active minutes are authored fixture values, not observed attention, interruption or recovery costs. No human, real notification, app, task data, or product policy is involved.

## Frozen gate

Source: `fixture.json`, `candidate.py`, `audit.py`, `test_method.py` in this directory. Candidate once; if exit 0, independently run auditor once. No retry, network, build, model, GPU, GUI, input or external service. Host construction CI is distinct from the OrbStack container allocation. Freeze git base and SHA-256 of all four files immediately before the reserved container run. Exact cached image must be `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` for linux/arm64; mismatch or no exclusive queue grant means STOP before candidate.

## Local construction failures retained

1. First CI found incorrect task/route coverage assertion (candidate required route-complete effects that fixture did not yet contain).
2. Second CI found the expected synthetic collaborator burden was mis-added (19 claimed vs 18 in source rows), and burst mutation lacked an explicit cardinality gate.
3. Third CI showed the independent audit didn't compare candidate no-response output, so an erased response state passed the audit.
4. First route-indexed CI caught a denominator error: 18 minutes was the sum across both routes; the fast-route burden is 17, versus 1 on plain. The route-specific result is now asserted.
5. Mutation controls were updated to accept the candidate's explicit fail-closed `event_status_count` rejection as the expected gate.
6. The route-indexed host-run-02 did not report maximum/burst burden. Its raw and 10-check PASS are preserved but superseded as `AUDIT_INCOMPLETE`; current version adds event `burst_id` grouping and a principal-indexed maximum-burst output.
7. The first explicit maximum-burst unit-test expected 3 minutes for collab-b, but the fixture's six-minute cleanup is the larger singleton burst; the deferrable-alert burst remains three events/three minutes. The assertion now checks maximum count and maximum effort separately.
8. Final review found set-based task×route coverage could admit duplicate pairs, and the auditor's hand-entered check count was not the number of executed checks. Candidate and independent audit now require exactly one effect row per pair; audit reports runtime check counts by category.

These were pre-freeze construction failures, not experimental outcomes. Corrections are in current files. Final local CI result is recorded separately; container gate remains not run pending an owner-bound OrbStack slot.
