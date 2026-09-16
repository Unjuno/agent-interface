# Socket producer readiness gate v1

Decision: **PASS_SOCKET_FIRST_RECORD_READINESS_SCOPED**.

## Result
The frozen 12-case formal block ran exactly once with zero reruns. Under the unchanged 50 ms EventCursor read timeout and the same delayed producer, exact v11 `endpoint_only` exposed the preregistered readiness race in **6/6** cases: every action/request read returned `timeout` with zero records and `authority=none`. `first_record_gate` reached the exact scoped `effect_evidence` boundary in **6/6** cases with one record and `authority=none`. The candidate published its endpoint only after the first record had been parsed and appended in all six formal cases.

Construction controls were frozen before formal: exact current-main upstream Git blobs matched **6/6**, unit tests passed **6/6**, silent producer returned bounded `observation_socket_unready`, and malformed producer did not create false readiness. The independent postformal audit reports zero errors and rehashes every frozen source exactly.

## Timing interpretation
This is **not a latency speedup**. Median endpoint-availability wait moved from 488.674 ms (`endpoint_only`) to 1071.218 ms (`first_record_gate`). Once the candidate endpoint was advertised, its median read time was 0.594 ms versus the baseline timeout at 50.689 ms. First-record append to endpoint publication was 0.070 ms median. The mechanism changes when readiness is claimed; it does not remove producer/startup latency.

## Interpretation
This supports #797's retained diagnosis for its single-record fixture: advertising a usable observation endpoint before producer publication can spend the caller's bounded read budget on producer startup rather than event waiting. A bounded first-record gate prevents that specific false-ready state without lengthening `read_until()`.

Do **not** promote this as generic socket semantics. A persistent runtime may need command forwarding before any observation exists, and the first record may be unrelated to a later awaited boundary. The next integration question, only if the real caller needs it, is an explicit producer-ready or event-specific readiness contract rather than gating every socket on first output.

## Integrity
- publication base `2adef46f497ed74729b93ea67cf93928df992e52`;
- preformal FREEZE SHA-256 `9b5bd223fabc064df78ec836f207647615f3f9e7b2f7af063956ecc113a68170` committed remotely before formal;
- formal rows 12, invocations 1, reruns 0;
- RESULT SHA-256 `d38c151055ad41e94cac9165d7783f160a81000d4b1f5a2091edae3880861f02`;
- AUDIT SHA-256 `981b48dded76c582c3417f3c73f3784dc7b87b1d0dc7dfcb9eaa6de451f064e7`;
- no GUI/model/provider/network task/input authority or production runtime mutation.
