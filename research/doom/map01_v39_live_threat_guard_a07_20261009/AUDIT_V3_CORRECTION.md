# A07 audit-v3 temporal admission correction

## H/T/D/C/U

**H — Hypothesis.** The v2 cancellation join can count an input admission by identifier even when the admission occurs after that cancellation, allowing malformed custody evidence to report scoped `PASS`.

**T — Treatment.** Replay a synthetic matched cancellation with a later same-ID admission, verified release transition, empty input-release event, empty terminal, in-window hard-health guard, and useful scorer event. Then require the new v3 reconciliation to reject this ordering. Also test monotonic timestamps and delayed event publication.

**D — Result.** A single regression runs the same fixture through both auditors: unmodified v2 returns `status=PASS`, `scoped_pass=true`, and `input_admitted_before_cancel=1`; v3 returns `status=FAIL` and counts the row as a post-cancel admission. V3 also rejects a contradictory `admitted_ns > requested_ns` timestamp while accepting delayed publication when `admitted_ns < requested_ns`. Missing one side of a timestamp pair fails closed; when neither timestamp exists, append-only JSONL order is used.

**C — Scope.** These are temporary synthetic files. They test cancellation-to-admission ordering in the scoped custody reconciliation and do not re-audit the saved A07 runtime traces.

**U — Limits.** `formal_pass` remains false. This does not establish that the retained A07 run contains an out-of-order admission, physical release, task effect, guard efficacy, recovery, or gameplay success. The prior v2 source, tests, and saved result remain unchanged; v3 writes `AUDIT_V3.json` separately and records the original audit digest plus the v2 result digest when present.

## Verification

```text
python3 -B -m unittest test_audit_live_v3 -v
Ran 16 tests ... OK
python3 -B -O -m unittest test_audit_live_v3 -v
Ran 16 tests ... OK
python3 -B -m py_compile audit_live_v3.py test_audit_live_v3.py
git diff --check
```

The counterexample is preserved as `test_input_admitted_after_cancel_cannot_pass_custody`; the original v2 false-PASS was reproduced before introducing v3. No live output was read or changed during this correction.


## Malformed event-ID fail-closed follow-up

A review of the exact v3 head found that an unhashable ID (for example, `[]`) in `cancel_requested`, `input_released`, or `terminal` raised from `Counter`/`defaultdict` before `AUDIT_V3.json` could be written. The v3 auditor now validates IDs for all five identity-bearing families it reconciles (`cancel_requested`, `input_admission`, `input_release_transition`, `input_released`, and `terminal`) before any indexing. Malformed rows are excluded from the reconciliation maps, the aggregate custody gate deterministically returns `FAIL`, and the additive audit output is retained with `all_relevant_event_ids_valid=false` and `malformed_event_id_rows` recorded.

`test_unhashable_identity_event_ids_fail_closed_and_write_audit` mutates each of the five event families and asserts exit code 1, a written audit file, `status=FAIL`, and the explicit malformed-ID diagnostic. The complete suite passes 16/16 normally and under optimized Python. No saved A07 allocation or `AUDIT_V3.json` was opened, rerun, or modified; `formal_pass` remains false.
