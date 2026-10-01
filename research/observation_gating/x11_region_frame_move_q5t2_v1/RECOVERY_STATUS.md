# Recovery status for #4439 allocation 01

The original source, plan, report, result, audit and available evidence fragment
are preserved unchanged. Their scientific disposition is unresolved because the
authoritative records conflict and the raw publication is incomplete:

- The current #4439 Issue body says the original local allocation stopped
  before case 0 and that its STOP receipt remains on this v1 branch.
- The v1 branch's `REPORT.md` and `RESULT.json` instead claim
  `PASS_X11_REGION_FRAME_MOVE_BOUNDARY_SCOPED` for 27 formal cases under the
  same allocation ID. This recovery cannot reconcile those records.
- `EVIDENCE_MANIFEST.json` requires parts 01–05 for a 27,628-byte archive, but
  only `evidence.part05.b64` is present in the branch. Running the frozen
  unpacker stops on missing `evidence.part01.b64`; the raw-only audit therefore
  cannot be independently reproduced from the branch contents.
- The distinct v2 successor result is already merged by PR #4903. It remains a
  separate allocation and is not evidence that resolves the v1 record conflict.

No scientific rerun, result rewrite, or missing-part reconstruction was made.
Disposition for this recovery: `HOLD_CONFLICTING_RECORDS_AND_INCOMPLETE_RAW`.
Treat the v1 PASS and audit as historical reported claims only until the owner
supplies the complete archive and resolves the Issue/branch chronology.
