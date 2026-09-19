# ERROR CHECK

- Same task/model/live allocation rerun: **0**.
- Existing v38/v39 result mutation: **0**.
- Source-first freeze before compute: **yes** (`51255221771f35652ffe1bbb68ed20a07f36b8c7`).
- Frozen retained-input SHA mismatch: **none observed before analyzer failure**.
- Existing analyzer regression tests before full computation: **7/7 PASS**.
- Full computation completed: **no**; stopped on partial-admission hold state.
- Aggregate occupancy result claimed: **no**.
- Temporary workflow merged: **no**; deleted before PR.
- Workflow supervision defect hidden: **no**; documented in `RESULT.md` / `ACTIONS_RUN.md`.
- Scientific disposition: **FAIL_INTEGRITY_ANALYZER_COVERAGE**.
- Required next action: new task identity with preregistered partial-admission interruption semantics; do not repair this result in place.
