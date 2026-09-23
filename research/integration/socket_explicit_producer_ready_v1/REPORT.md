# Explicit producer readiness gate v1

Decision: **PASS_EXPLICIT_PRODUCER_READY_SCOPED**.

## Result
The frozen 12-case formal block ran exactly once with zero reruns. Exact v11 `endpoint_only` timed out **6/6** under the unchanged 300 ms EventCursor read budget and reached no `effect_evidence`. `producer_ready_gate` reached the later exact action/request-scoped `effect_evidence` boundary **6/6**, with one observation-only `producer_ready` record followed by one effect record and `authority=none` on every read result.

The candidate did **not** wait for the effect before advertising the endpoint. Across all six candidate cases, ordering was exact `producer_ready emit -> EventCursor append -> endpoint publication -> effect emit`. Endpoint publication led effect emission by 149.859 ms median (range 149.784–149.924 ms), while ready-append to publication was 0.076 ms median.

Construction controls were frozen before formal: exact current-main upstream Git blobs 6/6, unit tests 7/7, silent producer bounded-unready, malformed JSON bounded-unready, and a `producer_ready` record with non-`none` authority bounded-unready. Independent postformal audit errors: 0; every frozen source rehashes exactly.

## Timing interpretation
This is **not a speedup claim**. Median endpoint-availability wait was 449.086 ms for exact v11 versus 917.465 ms for the explicit-ready candidate. After endpoint availability, the baseline spent 304.491 ms and timed out, while the candidate spent 150.495 ms waiting for the deliberately 150 ms-later effect and reached the boundary. The intervention changes when the endpoint is truthfully called ready; it does not remove process startup or effect latency.

## Interpretation
This strengthens #802's scoped finding. A producer initialization milestone can be separated from later event availability: the caller can begin its bounded event wait only after producer startup is confirmed, without waiting through the event itself and without increasing the read timeout. This is a cleaner candidate than first-record gating for a persistent caller **when a natural producer-ready milestone already exists**.

Do not promote `producer_ready` as a new production ABI event from this synthetic fixture. The marker is authored instrumentation, same-user local AF_UNIX only, and the real persistent runtime may have a different existing initialization milestone. The next high-information step is to locate and test that existing real lifecycle milestone; if none exists, stop rather than inventing another readiness vocabulary.

## Integrity
- publication base `2adef46f497ed74729b93ea67cf93928df992e52`;
- canonical preformal `FREEZE.json` SHA-256 `897823f7972d8f4b6a85dd2f376c81e24146520476005e524c94270587074f42`, Git blob `3788c47dd9c80ff8544fe7606265609c77dca118`, committed before formal at `d44b4c99614147cdb335ead33bb74c7f59a10658`;
- exact preformal source archive SHA-256 `2c4c5b3828db3f0becc0f1578f04bbda1c5d91e8db567930742e0d098e391fdc`, with remote base64 blob `c00583864d5a01659116a8d9976e8432f0df68eb`, also published before formal;
- remote readback matched canonical local blobs for FREEZE, PREFLIGHT, plan, prereg and source archive before formal;
- formal rows 12, invocations 1, reruns 0;
- RESULT SHA-256 `27148cb9b3d555035f46248949d4fa39537555f4ac9146d36ea1182f4a3cbe0d`;
- AUDIT SHA-256 `3334de511c2c40eedf8f757874ab7bca80e511a8a0250e94f4879a80c2067682`;
- no GUI/model/provider/network task/input authority or shared runtime mutation.
