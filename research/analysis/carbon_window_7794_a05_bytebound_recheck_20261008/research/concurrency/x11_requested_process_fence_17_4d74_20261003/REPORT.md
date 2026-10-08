# Requested process fencing before cancel acceptance — #7034

First outcome: **SCOPED_REQUESTED_PROCESS_FENCE_SUPPORTED**; **HOLD_RUNTIME_PROMOTION**. This includes a concrete keepalive counterexample, not a blanket cancellation guarantee.

The separate supervisor released F8 and recorded acceptance while the task child remained paused after its positive F9 check. A fresh +151ms keymap checkpoint was neutral, yet resumed child started the actual public F9 native wrapper **400.197388ms after acceptance**. Neutrality at one checkpoint is not proof of future input exclusion.

The reference killed and reaped that exact Python child, observed stdout pipe EOF, THEN recorded acceptance. F8 remained held in an independent post-reap query (start4705788967/end4705886300ns; reaped4705786658ns), and the cleanup plane then released it. No F9 native call or app press occurred. The killed dispatch had exit-9 and **no public completion receipt**. Future task continuation was lost.

| Arm / context | Owner exit | App press/release trace | Request→accepted | Request→F8 keymap-neutral readback |
|---|---:|---|---:|---:|
| keepalive / healthy | 0 | F8↓ F9↓ F8↑ F9↑ | no cancel | no cancel |
| keepalive / paused | 0 | F8↓ F8↑ F9↓ F9↑ | 0.000756ms | 0.302182ms |
| terminate-before-accept / healthy | 0 | F8↓ F9↓ F8↑ F9↑ | no cancel | no cancel |
| terminate-before-accept / paused | -9 | F8↓ F8↑ | 1.409431ms | 1.844544ms |

Four fresh private Xvfb instances, seven actual positive public native calls, fourteen application events,1064 independent whole-keymap samples with button queries. Every final sample neutral; emergency emissions0. Healthy arms returned genuine completed/accepted public receipts. Both paused checkpoints were fresh before +400ms resume; keepalive child alive, terminated child absent. Three WSLc stage containers are stopped/retained; no task/native/formal replay.

Source freeze [7550e7c721d421544207a128d865a412672d28e2](https://github.com/Unjuno/agent-interface/commit/7550e7c721d421544207a128d865a412672d28e2),20 actual Git byte images read back before input. All12 frozen source/PLAN/launcher files unchanged afterward. Six public runtime files are exact intake main effc43f8bd11f20f83c3410101c04f31c0c353f7 bytes, also identical to the prior study; neither historical result is replayed.

Producer first start12:09:56.4404848UTC→12:10:02.0847638UTC exit0/four cells. Separately implemented saved-only auditor first12:10:20.2776152UTC→12:10:20.7858396UTC exit0/errors[]. Raw SHA256 a74cda0795458416c64662e85f8b9d78bd1207fe719ed296afb3cb6385e0072d. Candidate mount excludes audit/oracle; auditor reads frozen source plus raw and original pipe byte images read-only. Root authored both implementations, so this is independent implementation/process reconstruction, **not external human review, an independent agent vote, or causal model/task efficacy**.

Pre-input WSLc construction first run3 tests PASS,11 hand-oracle corruptions plus missing-evidence rejection. Applicable current namespace CI22 tests PASS on actual Windows host Python3.11; exact six source images and tool-captured transcript retained. These are construction/namespace checks, not full repository CI or a fresh scientific run. Source/package review also confirms every change is additive/inert and no public runtime/workflow/default discovery changed.

Cached amd64 image sha256:865bfbcc86992769ec9b8311a2344b67c664639d96d7cf0d5c407df9c2c500ed; Python3.12.15. Networknone, user65534, requested1CPU/512MiB/tmpfs64MiB. Actual cpu.max100000100000,memory.max536870912,pids.maxmax; WSLc swap-limit warning retained. Configuration is not resource-enforcement proof. No Docker/GPU/model/host desktop inputs. Initial pre-input source transfer was rejected for exceeding64000-byte auto-review limit; unchanged per-file transfers succeeded. No code executed in rejected call, no formal allocation consumed.

## Interpretive limits and integration decision

Acceptance is an external research marker; the cached F9 positive permit and deliberate stdin pause are instrumentation. Public X11RuntimeSession has no cancellation contract here. Native timestamp brackets are wrapper boundaries, not kernel syscall/X-server queue entry. snapshot.end_ns brackets query_keymap; the button query occurs afterward. Therefore request→release readback numbers refer to the keymap query, not a fully timed pointer query. App receipt can lag injection; the late-input claim uses native_start, not app delivery time.

SIGKILL/reap prevents subsequent Python execution by this child, a source-determined property. The empirical additions are real death/EOF, XTEST state persisting after client death, independent release/readback, actual suffix/native/app ordering and healthy parity. This is a directed four-case test, not a failure-rate or hard150ms guarantee. No descendants/process-tree security fence, prequeued X requests, unresponsive X/compositor/GIL/kernel/host, bystanders, fresh scope reconstruction, restart/re-admission, physical keyboard sensing, useful feedback, task survival, token benefit or human-tempo claim.

#7024 separately owns dead-owner public release_all tracking reconstruction. This study fixes a prearmed cleanup scope in both arms and tests requested revocation before queued positive native input. Preserve #810/#821/#7010/#7012/#7024 unchanged; no pooled counts.

Next production decision must bind cancellation acceptance to retirement/revocation of all relevant task-input authority, AND independently confirmed cleanup, while exposing aborted task completion honestly. This reference is a reason to evaluate a broker/owned-task termination boundary, not to ship this wrapper or classify a killed dispatch as success. #17/#59/#57 and full ROADMAP stay open.

Archive .py.txt/.ps1.txt files are inert original byte images. Restore into a new private scratch directory for saved-only audit/constructor checks. Never rerun producer.py or the consumed run_once.ps1 producer phase. Commands and exact outcomes are in runs/*/HOST_RECEIPT.json.