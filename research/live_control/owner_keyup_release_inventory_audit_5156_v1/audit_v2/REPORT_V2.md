# #5156 PR #5502 request-parity audit correction — v2

## H / T / D / C / U

**H.** A separate audit of PR #5502's retained owner-behavior summary will
recompute the exact v10/v11 X request sequence from its recorded arrays against
the frozen six-request fixture contract, rather than trusting the runner's
`v10_v11_behavior_equivalent` Boolean. It will accept the pinned raw summary
and reject changed, equally-wrong, mistyped, or internally contradictory
request-sequence evidence.

**T.** Re-read and hash-pin the exact retained `RUN_BYTE_IDENTICAL.json` plus
the six-request sequence declared by the frozen runner. Keep the sibling
`expected_inventory.json` hash in the provenance record, but do not treat it
as an input to this narrower owner-behavior check. Do not invoke the owner
runner, formal allocation, or X11 fixture. Run six focused tests against the
additive v2 checker, then use its retained one-shot audit-only output with five
in-memory copied-evidence corruptions. Keep the original #5502 v1 source,
runner, raw, auditor, and result unchanged.

**D.** `PASS_REQUEST_SEQUENCE_PARITY_AUDIT_V2` requires a clean result on the
exact pinned raw, rejection of all five declared mutations, and all six tests
passing. The disposition is limited to this request-parity audit subgate.

**C.** The fixture is deterministic fake-Xlib output. The independently frozen
sequence is specific to its declared six requests; the check says nothing
about arbitrary owner histories. This second audit implementation is
same-author and does not establish independent human review.

**U.** This is not a new physical-input, real-X11, held-key occupancy, MAP01,
task-effect, or recovery experiment. The actual #5156 X11 allocation remains
unspent and awaits the explicit #5085 resource assignment. A scoped v2 audit
does not upgrade the original synthetic result to physical-input evidence.

## First-outcome and correction history

Before the v2 checker existed, an in-memory copied-evidence probe changed
`v10_requests` to `[]` and `v11_requests` to `[[99,999]]` while preserving the
submitted equivalence flag. The existing `audit_independent.audit` returned
`[]` for both pristine and mutated records. A test written against that
behavior failed as expected (`AssertionError: [] is not true`). This is the
retained RED discriminator; no source or raw result was changed.

The v2 checker was then implemented separately under this directory. The
retained raw passes with no errors; v2 rejects all five copied-evidence
mutations, and its test suite passes 6/6. The runner was not rerun, and no
formal, container, X11, model, GPU, game, GUI, or user-input action occurred.
The complete output and hashes are in `AUDIT_V2.json` and `FREEZE_V2.json`.

## Commands

```bash
python3 -m unittest discover -s research/live_control/owner_keyup_release_inventory_audit_5156_v1/audit_v2 -p 'test_*.py' -v
python3 research/live_control/owner_keyup_release_inventory_audit_5156_v1/audit_v2/run_audit_v2.py
git diff --check
```

The neighboring original PR's 14 fake-Xlib tests also passed 14/14 in this
checkout when invoked with the runner's `executor_v3` test stub. A direct
un-stubbed unittest import failed before tests ran; it is an invocation setup
issue and is not counted as a failed test. This correction does not change the
original PASS label's stated synthetic scope. PR #5502 remains Draft pending
external review; this author cannot submit a GitHub review on their own PR.
