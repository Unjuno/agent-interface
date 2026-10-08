# Construction history

- Attempt 1: `BUILD_FAIL`; release-field mutation was applied to a fixture whose expected release was already `UNKNOWN`, so the mutation was a no-op and the rejection assertion correctly failed.
- Correction: apply the release mutation to the `released_no_effect` history (`RELEASED` -> `UNKNOWN`). No formal A04 auditor invocation had occurred.
- Attempt 2: `BUILD_PASS rows=8 role_fields=56 mutations=5` in OrbStack Docker. Formal audit remains one-shot and has not yet run at the time this record is frozen.
