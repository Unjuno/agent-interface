# #6219 T0: amendment-conditioned effect ledger

Method-only deterministic CPU study; no model, GUI, participant, or user data.

**H:** For a frozen effect ledger, retaining source clauses and verified/UNKNOWN effects under an authenticated task amendment correctly distinguishes continuation, safe compensation, HOLD and impossible full satisfaction better than old-plan continuation, prompt reset, or blanket undo, with no stale proposal admission.

**T:** Replay the nine frozen synthetic amendment cuts in `fixture_public.json` across four policies. The truth table is independently specified in `oracle_truth.json`. Candidate and raw auditor are separate modules; auditor imports no candidate code. Four mutations test erased effects, old-generation proposal reuse, UNKNOWN-as-absent and silent compensation of an irreversible effect. Construction tests use only embedded construction fixtures.

**D:** PASS_METHOD_SCOPED only for exact oracle agreement, all policy rows, preservation of committed/UNKNOWN effects, unauthenticated amendment rejection, stale proposal rejection, and all four mutation rejections. No human or product claim.

**C:** Clause/effect mapping is fixture-authored; another application may represent revisions, transactions and compensation differently. A fully reversible task may make a ledger unnecessary.

**U:** Scripted amendments do not represent human intent formation. No live user, consent, model, GUI, task execution, or product benefit is tested.

## Execution

Construction (host-only, separate embedded fixture): `py -3.11 -B -m unittest -v test_method.py`.
Formal candidate and auditor each run once only, inside separate network-disabled WSLc containers after the exact start freeze and container/image gate are recorded. Use the already-cached Python image pinned by manifest digest `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`; never pull. Mount this package read-only at `/src`, with unique writable host outputs at `/out`. Use `--network none --cpus 1 --memory 1G --pull never`. Run candidate once, then give its raw JSON read-only to a separate auditor container. Preserve stdout/stderr, container metadata and output hashes. Configured memory limit is not evidence of effective enforcement. No retries.
