# Issue #59 — workflow-path owner pagination integrity T1

## H / T / D / C / U

- **H:** The current workflow-path-global owner helper can admit a formal run from an incomplete but apparently complete (`total_count == visible row count`) API response when the response has duplicate run IDs and omits another run, because it deduplicates by run ID before comparing the API total.
- **T:** Freeze the exact main helper/test source; rerun its full retained helper suite; enumerate a small run-visibility model over bounded run sets, page sizes, duplicate rows, and missing rows; compare helper decisions to an independent oracle that admits only when the full distinct workflow-path run set is known and current run is its canonical earliest owner. No live API request or Actions workflow is used.
- **D:** Confirm the defect only if at least one incomplete visible response reports `total_count == len(rows)`, passes existing completeness checks, and admits a current run while the independent full-set oracle rejects it. Refute within this bounded model if none exists. Any disagreement unrelated to incompleteness is `FAIL_ORACLE_DISAGREEMENT`.
- **C:** GitHub's API semantics may define `total_count` as matching distinct runs, not raw rows, and normal pagination may not yield duplicate IDs across pages. The synthetic model establishes a parser/contract weakness only if such payloads are admissible; it does not establish that GitHub actually emits them.
- **U:** No network, workflow dispatch, concurrency race, Actions pagination behavior, MAP01/game/model/GUI/input, Docker, or live allocation is exercised. A PASS identifies only a fail-closed completeness weakness in the helper's accepted payload model; it is not a live duplicate-run reproduction.

## Frozen source

- Main intake: `5eb0c44f2fc3d851b6469ceabda57b091ec76668`.
- Helper: `research/orchestration/o3-g7/global-owner/formal_allocation_global_owner_v1.py`.
- Test: `research/orchestration/o3-g7/global-owner/test_formal_allocation_global_owner_v1.py`.
- No external service, model, user input, container, or GPU.
