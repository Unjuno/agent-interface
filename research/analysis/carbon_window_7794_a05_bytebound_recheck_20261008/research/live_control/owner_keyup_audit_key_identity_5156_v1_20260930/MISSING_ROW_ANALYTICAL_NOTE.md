# Omitted-row analytical check for the frozen key-identity candidate

Date: 2026-09-30  
Disposition: **ANALYTICAL_REJECTION_ESTABLISHED_FOR_PINNED_OMITTED_ROW**

This note addresses the omitted-row coverage raised in
[Issue #5486](https://github.com/Unjuno/agent-interface/issues/5486#issuecomment-5911473437).
It does not add an executed test to #5489's historical seven-test record and
does not import #5492's PASS as execution evidence for this candidate. No
candidate, runner, auditor, container, model, GUI or allocation was executed
for this source-and-data proof.

## Exact source and assumptions

Reviewed #5489 head: `82327db213b8fbd4d2d4c86dd312a26ebb792ab1`.
All paths below are relative to
`research/live_control/owner_keyup_audit_key_identity_5156_v1_20260930/`.

| Object | Git blob | SHA-256 |
| --- | --- | --- |
| `audit_v3.py` | `d98e0759e1a0b7768c87e0e2bfc07a3ab18407aa` | `9cc331d0fbce72267904341e1163a5c518f36fd2f47a651756e7f579427dc2d0` |
| `expected_inventory.json` | `affa71e53457bb903353ce67b3477ef20b1d488c` | `9ef72a837ce4f5d802dcc7fdb72a843a0e768154dbe30897a00f270cfaabde2b` |
| `raw_input.json` | `451247a5180348b8c29d09994dc0264f822585d1` | `56842934b9f9b13fe0e52d515d31bd0c3d598cdb1cfa8b719dfb4c8ba463cbc2` |
| `test_audit_key_integrity.py` | `79fec65a34efe83ad054b4ea6a795650569ded4c` | `72d06a37a076ecf03a69861086da7900ee33c35053dc3e140059bb23199b3ad0` |

Complete retrieved bytes recreate these Git blob identities and SHA-256 values.
The proof assumes normal Python list/dictionary/Counter semantics, successful
parsing of these exact JSON inputs, and the expected inventory held unchanged.
Only the first raw record is deleted, without modifying either surviving row.

The expected release IDs are distinct, each occurring exactly once:
`explicit-a-01`, `explicit-a-02`, `cleanup-b-01`. The deleted first record is
`explicit-a-01`; the remaining raw order is `explicit-a-02`, `cleanup-b-01`.

## Complete error-path argument

1. The expected inventory is a nonempty list; the shortened raw value is still
   a list. Neither initial-return guard applies
2. All three expected entries are dictionaries satisfying `_valid_identity`.
   Their release IDs are unique, so no expected-identity or duplicate-ID error
   is appended
3. Both surviving raw rows are dictionaries with event
   `owner_key_release_bracket`, schema `owner-key-release-bracket-v2`, and all
   required identity, timing and Boolean fields. Their logical keys are the
   valid explicit string `a` and explicit cleanup null. No missing-field,
   invalid-identity, event or schema branch appends an error
4. The explicit row's timing is `220 <= 230 <= 235`; the cleanup row's is
   `320 <= 330 <= 335`. All are integers. Both rows have `timing_valid:true`,
   `grants_input_authority:false`, and `physical_key_up_claimed:false`.
   No timestamp or Boolean-gate error is appended
5. The raw loop therefore appends exactly `explicit-a-02` and `cleanup-b-01`
   to `actual_ids`. `expected_counts` has count 1 for each of the three IDs;
   `actual_counts` has count 1 for the two survivors and returns default zero
   for absent `explicit-a-01`. At candidate lines 83–85, `0 < 1` necessarily
   appends `expected_release_missing:explicit-a-01`
6. Each surviving ID has actual count equal to expected count, so there is no
   additional missing/duplicate error. The actual-ID set is a subset of the
   expected-ID set, so there is no unexpected-release error
7. The final identity comparison covers only IDs present in both maps. Every
   surviving seven-field identity is unchanged and equal to its corresponding
   expected identity. It appends no mismatch error

Consequently the exact returned error list for this pinned omission is:

`["expected_release_missing:explicit-a-01"]`

This is a source-level conclusion, not a newly observed runner output.

## Relationship to the two retained constructions

#5489's seven committed tests and separate pristine audit do not delete a whole
row. Its [later independent review](https://github.com/Unjuno/agent-interface/pull/5489#issuecomment-5911345611)
confirms nullable-key identity using five key-field mutations; that result remains
valid and distinct from this omitted-row proof.

The separately preserved #5492 runner at head
`0cd0c56681eee47e81852d29a2f461c81c319d03`, blob
`770d7ccb82c09ea4ac60db060ccde7563308028b`, constructs its missing-row control
by copying the same raw fixture and applying `pop(0)`. Its candidate blob
`05908365ddb19baf19e5a80890e8f882dc13346b` differs from #5489's candidate.
The two files have identical `audit` function bodies; their identity helpers
agree on this fixture. Tuple field order differs but does not affect equality
for these unchanged surviving identities. Thus this exact omitted-row rejection
agrees analytically with #5492's retained error, without transferring its
execution or acceptance status. Global implementation or diagnostic-string
equivalence for arbitrary inputs is not claimed.

#5492's independent_audit_v2 checks runner decision JSON and declared Boolean
outcomes, not the original raw rows or source-hash values themselves. Preserve
its historical audit label with that scope, separately from current byte checks.

## Remaining boundaries

The omitted-row behavior is decidable from the pinned code; no scientific rerun
is needed. Whether this reviewed analytical equivalent satisfies #5486's
integration criterion is a separate explicit review decision. The historical
seven-test count, original raw, freeze and both allocation outcomes stay unchanged.

Trust in the expected inventory remains an assumption. This proof does not
detect coordinated omission from both inventory and raw, establish complete live
InputOwner emissions, physical key-up or held-input timing, X11/MAP01 behavior,
recovery efficacy or useful task effects. The live resource/allocation gates
remain open.
