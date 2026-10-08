# Scorer endpoint readback type guard — A01

Status: `HOLD_STUB_CONTRACT_MISMATCH`.

## H/T/D/C/U

- **H:** The pinned #7685 candidate's post-snapshot episode-time check accepts non-integer readback values if Python equality aliases them to the acknowledged integer endpoint.
- **T:** Freeze exact candidate source bytes and execute three stub cases: valid integer control, float alias, and Boolean alias. Independently inspect pinned source identity and saved case outputs without importing the candidate.
- **D:** Fail-open if either malformed endpoint receives `REFRESH_RETURNED_RUNTIME_QUALIFICATION_PENDING`; pass-fail-closed only if the integer control qualifies and both malformed endpoints return `UNKNOWN` without score values. Hold on hash/audit mismatch.
- **C:** Official API results may always be exact integers; the test addresses defensive contract enforcement only.
- **U:** Deterministic stub construction against a non-integrated pull-request candidate. It is not a live game, scorer, input, or controller result.

Exploratory reproduction against the prior PR head `85b6ebbcaef769ef4a997d9d86c8b44160afebd8` found the float alias accepted. Before freezing this successor, the PR head changed to `5b4a563b5c3f6a70a063a98c7281a8bd6ce71eb0`; this A01 tests only that new, hash-pinned source snapshot.

The candidate invocation returned exit 0 but did not reach the endpoint-readback guard: all three cases failed at the newly added `get_available_game_variables` ordering check because the test stub omitted that method. The runner labeled this a PASS because its decision rule did not require the integer control to qualify. This is a harness/decision-gate failure, not evidence about endpoint type handling. Independent audit was not run. The exact raw first output is retained in `RESULT.json`; do not rerun this allocation. A corrected harness requires a new versioned construction test.
