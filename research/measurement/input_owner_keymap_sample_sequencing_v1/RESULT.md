# Issue #1030 first construction outcome

Decision: **`FAIL_CONSTRUCTION`**.

The first frozen 500,000-case construction retained **0 non-sample semantic/state mismatches** and **0 sample-failure semantic changes**, but failed the preregistered ordering gate in 4,939 cases. Independent audit on 100,000 fresh seeded cases reproduced **0 mismatches** and 983 ordering errors, so the first outcome remains FAIL rather than being upgraded post hoc.

## Diagnosis

The fixed case `key_unavailable_up` already isolates the failure: both baseline and candidate stop immediately after `key_lookup=false`, before `held_owner_check` and before any physical sample. Their traces and terminal state are identical. The frozen `check_order()` branch for UP-without-`sample_pre` incorrectly requires `held_owner_check` even when key lookup itself rejected the operation.

The random failure rate is consistent with the frozen generator's `P(up)=0.5` and `P(key_available=false)=0.02`: expected about 1% of 500,000 cases, observed 4,939 (0.9878%); audit observed 983/100,000 (0.9830%). This diagnosis does not change A1's disposition.

## Preserved evidence

- random cases: 500,000
- non-sample mismatches: 0
- ordering errors: 4,939
- sample-failure cases: 95,046
- sample-failure semantic changes: 0
- case digest: `d71e58c41a84f463aa7f224f02ae143b859fb7a8292a3507d2a01b15b67e4269`
- audit cases: 100,000
- audit mismatches: 0
- audit ordering errors: 983
- audit digest: `4a1fc472d484b74e978feb6a9c7a9744314171fc6f69aaf3c7ec1d4dafad014c`
- raw local `RESULT.json`: 25,981 bytes, SHA-256 `5ab5faef405c4f13a33a7667ff3b0de64d479d3e4225835610ba6ad03c7ee901`; not falsely claimed Git-retained.

## Disposition

`STOPPED_A1_ORDER_AUDITOR_SCOPE_BUG`. Do not tune candidate mechanics or pool a repair into this result. The smallest successor changes only the ordering auditor so a key-lookup rejection is accepted as a valid pre-sampling terminal for both DOWN and UP; all candidate/baseline logic and scientific H/T/D/C/U otherwise remain frozen under a new task identity and fresh corpus IDs.
