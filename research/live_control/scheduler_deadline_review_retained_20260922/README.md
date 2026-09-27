# Retained deadline-audit review for #3934

Retrospective engineering evidence under #3934/#2547, not a new scheduler experiment or a production patch. The 28-case review was locally source-frozen and executed in the preceding conversation when the available GitHub connection had no write operations. Publication on this branch occurs afterward; it is not GitHub preregistration. All 168 original files are preserved. Their historical publication-STOP fields remain verbatim and describe the earlier connection, not the current delivery.

## Result and decision

`CONFIRMED_EARLY_WAKE_AUDIT_GAP`, scoped to the exact `reconstruct()` helper. Original source commit `4489206e9652ccce269b8d0a0c0597f196de8353`; audit Git blob `4ac8302a7e4db654f97a5bd2fa665f2e831f4e6f`, SHA-256 `8e382c1cdc76272e1db177f9773e766d89eebd649fd256b77abe437927f912c2`.

The helper checks signed delay arithmetic but does not reject wake-before-due records; its statistics clamp negative delays to zero. The additive guard retains all old checks and adds that missing ordering check. All input timing/PID rows below are synthetic; actual worker process receipts are retained separately.

| Fixed input class | Cases | Original helper | Original plus guard |
| --- | ---: | --- | --- |
| Valid/boundary controls | 5 | Accepts 5 | Accepts 5; full return objects unchanged |
| Deliberate early wake by 1 or 5 ms | 9 | Accepts 9 | Rejects 9 |
| Inherited invalid-evidence controls | 14 | Rejects 14 | Rejects 14; original errors preserved |

One original review orchestration, 28 actual fresh worker processes, all exits 0, zero reruns/replacements. The separately implemented raw verifier reported zero errors. Eight post-result verifier-corruption controls were rejected; five construction tests passed. Independent implementation/process means the same author's separate code, not external human review.

**This does not retract #3934's real timing PASS.** Its original raw timing archive was unavailable in the inspected source-only branch; it has not been independently reaudited here. The synthetic finding establishes a missing regression check, not that the real observations violated it. The added guard is engineering evidence, not a modification of any frozen auditor or shared runtime.

## H / T / D / C / U

H: arithmetic consistency after clipping is insufficient to validate deadline order. T: the fixed 5/9/14 case matrix above, exact upstream helper, local source freeze, independent raw verification; provided Linux x86_64 container and CPython 3.13.5. D: preserve every valid return object and inherited rejection, reject all nine early cases, and reconcile all 28 actual worker receipts. C: synthetic timestamps are not live scheduler samples; this exercises the aggregation helper, not the original complete file-level audit. U: no natural incidence, real-run revocation, clock calibration, speedup, GUI/model usefulness, production adoption or Docker/OrbStack image-attested replication. Millisecond violations are directed controls; a possible sub-resolution tolerance needs its own explicit contract, not a silently introduced epsilon.

## Exact retention and read-only reproduction

Eight Base64 text parts encode one 39,964-byte XZ capsule. SHA-256: `0e1842978fabbff940b859a2d2cfad808cdae0ef215f662bc16d4ab538f6d30c`. `CAPSULE.json` binds ordered decoded parts, expanded bytes, and member count. The storage transform is reversible: it retains signed integer-table residuals and exact JSON formatting, not a replacement generated from the experiment's expected answers. Every restored file must match its original size and SHA-256 before any file is written.

`unpack.py` restores 168 original files / 4,692,380 bytes and executes no archived code. The original delivered ZIP has SHA-256 `c73c9066ddcb530b83ec93ae3b5e1e53f4acc361fd5796700fd4f026f410a42d`; the ZIP container itself is not reproduced, but all its file contents are. Some original gzip encodings are reconstructed using the current Python/zlib compressor and then checked exactly. Tested with CPython 3.13.5; an incompatible encoding fails closed rather than silently substituting bytes. Hashes are integrity commitments, not publisher authentication.

From this directory, with a fresh destination:

```sh
python -B unpack.py /tmp/deadline-3934-review
cd /tmp/deadline-3934-review/research/live_control/scheduler_deadline_review_3934_v1
python -B verify_retention.py
python -B verify_review.py . review-01 > /tmp/deadline-3934-audit.json
cmp AUDIT.json /tmp/deadline-3934-audit.json
python -B -m unittest -v test_construction
```

Do not run the consumed `run_review.py`, `supervise_review.py` or original timing runner. Original audit SHA-256 is `96830fbd27d208420e6f7522023079503322447b8e455f62308ebd1c7ab02cf7`. Source freeze SHA-256 is `5a09b70e1eb967139c0dea6bafc339b10ebd08dc6ef5fa578c86fa0951bc2d55`. The full PLAN, source, compressed input rows, worker stdout/stderr and observed exits, audit, controls, failures and historical handoff are inside the capsule. `deadline_guard.py` and the unmodified `ORIGINAL_RESULT_SUMMARY.json` are also directly readable.

This delivery rechecked 167 manifest entries, five units, and byte-identical raw audit output without another review or timing allocation. Fresh capsule restoration matched all 168 original files; six packaging refusal controls passed. `PUBLICATION_CHECK.json` records these posthoc checks. Remote CI/review/main merge are separate gates and must be checked on the actual PR head.

## Separate #2547 failure preserved, not pooled

A different preceding local timing attempt remains `FAIL_MEASUREMENT_BINDING`: 90 cases, 180 null child-inventory fields, unchanged auditor exit 1 with 150 errors. Its full 274-file ZIP remains conversation-hosted, SHA-256 `f6fcf01e9280871b761990528cb279c9f32b6f56c8207bf95e42291ac4fa5787`; it is NOT in this capsule or claimed fully published here. This continuation verified its 273 manifest entries and reproduced the same failed audit read-only. Result/stop chronology was recorded in #2547 comment 5768681899. It is a local evidence limitation, not a refutation of #3934 or a fleet-wide research blocker.

## Integration boundary and roadmap

Intake base `2308b8301d69b7089a2e0636486736ed59b61537`; README, CURRENT_GOAL, ROADMAP, failure-routing rules, current Issues/PRs and branch inventories were checked. Existing scheduler/pause/timerfd/capture allocations are not duplicated. Only this new retained-evidence directory changes. Broad #3934/#2547/#57/#2789 and the repository ROADMAP are not closed by this delivery.

Remaining qualified step: when #3934's exact original raw bytes are available, run a separately labelled read-only deadline-order review and preserve its original verdict regardless of the new finding. Do not regenerate missing raw bytes by repeating the timing experiment. Evidence delivery proceeds through one additive PR, exact-head checks/readback, and own-branch cleanup only when supported and dependency-safe. No new auditor/supervisor research Issue is required.
