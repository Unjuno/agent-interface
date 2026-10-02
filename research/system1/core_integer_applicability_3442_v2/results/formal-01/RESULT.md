# Formal allocation 01 — result and disposition

## Outcome

**HOLD / auditor gate failed; no scoped PASS claim.** The frozen candidate
completed once with exit code 0 and emitted all 390 rows. The separately run,
frozen raw-only auditor completed once with exit code 1 and reported
`FAIL_OR_HOLD`. Its ten corruption controls all rejected their mutations, but
its row gate reported `operation index mismatch` on every in-range accepted
operation row.

Inspection of the preserved raw rows and frozen sources identifies an auditor
expectation defect: `FIELD_SPECS` assigns an operation index for each operation
field, and `audit_row` unconditionally requires that index. The runtime records
`operation_index: null` on successful validation and assigns the actual index
only to a raised operation-level `ContractError`. Thus the accepted operation
rows conflict with the auditor's expectation by construction. This is an
auditor/gate failure, **not evidence that the candidate hypothesis passed or
that the runtime is defective**. The frozen allocation is one-shot: neither
candidate nor auditor was rerun or edited, and the auditor output is not
reinterpreted as a pass.

## Process evidence

- Candidate: one invocation; exit 0; stdout `rows=390 raw_sha256=f6a82afed906bdd7a7eb46539d59cc53c24a0b89a17cdc154d86531e5a41fdf7`; stderr empty.
- Raw: 390 JSONL rows; SHA-256 `f6a82afed906bdd7a7eb46539d59cc53c24a0b89a17cdc154d86531e5a41fdf7`.
- Auditor: one invocation after candidate exit 0; exit 1; stdout `disposition=FAIL_OR_HOLD rows=390 controls=10/10 raw_sha256=f6a82afed906bdd7a7eb46539d59cc53c24a0b89a17cdc154d86531e5a41fdf7`; stderr empty.
- Audit JSON SHA-256: `ea301512bc3560d7c209da9ed909e885836fa85095e22b26cccef29592ae0581`.
- Auditor's frozen source SHA-256: `0265f9d9bf536c4e7dc809505912ff22cf48d2e2b5166d07bb0943b22eeec5d0`.
- Environment: host-local macOS 26.6.2 arm64, CPython 3.13.14, standard library. No container, GUI, input, backend, provider, model, or network was used by either process.
- Source identity supplied to the run: frozen main `40885011a5d8e15ab10bb6cc0e8eef65661718ee`; contract SHA-256 `4ad7e4426148688b8ece0ffbc4e95527b3697c08c84e5d0ab23a84f364574dc2`.
- Immediately before execution, main was observed at `8144e81cd134b35808884b53ac6503dbacd69902`; its intervening commits did not change the frozen contract or package-init blobs. No raw existed before candidate invocation.
- Captured in-session completion time: `2026-10-01T02:09:56Z` (candidate and auditor ran sequentially immediately before this capture; individual process start/end timestamps were not instrumented).

## Interpretation boundary

The row distribution is 156 accepted / 234 refused (78 accepted and 117
refused in each mode); the frozen auditor found all 10/10 corruption controls.
These descriptive observations do not override the failed audit gate. The
scientific disposition remains unresolved. Do not amend this allocation's
frozen runner/auditor, do not rerun either one-shot process, and do not claim
the proposed scoped runtime disposition. Any future attempt requires a clearly
identified successor allocation with an auditor contract that expects a null
operation index on successful validation, and must retain this raw and failed
audit unchanged.

## Follow-up

Keep the candidate raw and failed audit as immutable evidence. Report the
auditor defect and HOLD to Issue #3442. No PR or merge is justified by this
allocation. Continue recovery work on other branches independently.
