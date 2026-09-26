# Resident static validation cost: Issue #4364

## H / T / D / C / U
H: reuse of an unchanged static-validator process reduces cold-inclusive repeated validation cost, without a verdict cache, stale file reads, altered diagnostics, or action authority.
T: Linux x86_64, CPython3.13.5, standard library. CPU affinity is set to the smallest currently allowed CPU in each batch and inherited by children; load/frequency are not controlled. The same worker.py processes either one request per process (fresh) or an entire finite sequence (resident). Both load the same exact five main-matching modules; no backend, source rewrite, CLI monkeypatch, or result cache. The research entry is not the official CLI/MCP launch path. Mutable input path is owned/quiescent during each request.
The eight fixture states are in FIXTURES.json: observe, bad Boolean width, corrected width, file absent, malformed JSON, Unicode text-gap, over-capacity repeat, release-only. Every request first rewrites/removes the SAME file path. Requests are synchronous, one outstanding; reports are serialized identically. A worker never dispatches the programs it inspects.
Lengths1/8/32 x7 paired technical repetitions=21 measured pairs,42 sequences,574 responses,308 workers. Each length begins with one retained excluded warmup pair (82 responses,44 workers in total). Trial order is resident/fresh at warmup and odd trials, fresh/resident at even trials. All sequences start cold; no preload outside timed lifetime. Source, fixtures, auditor and gates must be public and exactly read back before any measured batch. Run each length once via launch.py; stop if the batch is incomplete. No exclusion, retry, replacement or tuning.
D: semantic/integrity gate requires all pairs/counts/exits, exact fixture/oracle/output parity, same-path updates visible, inputs unchanged, no input/task authority, frozen source/audit success and eight effective normal-rejection corruption controls. Cost gate: median of paired resident/fresh total wall ratios <=0.50 at BOTH8 and32. Length1/first response are reported without a speed gate. Complete semantic mismatch is FAIL; missing evidence is STOP/HOLD; correct semantics but cost miss is HOLD_COST_TRADEOFF. Validation rejection is a report, not worker failure. The first 8-step construction had a path bug and remains separate; see CONSTRUCTION_INCIDENT.md.
C: mode changes process/interpreter/import lifetime, not only an abstract startup constant. More persistent deployments may have queueing, memory growth, stale code or cross-request contamination. This finite serial fixture does not certify them. Positive controls prohibit all-rejection shortcuts. Existing validator's static-expired-lease semantics stay unchanged.
U: technical timing variability, warm filesystem caches, CPU frequency/scheduling and this interpreter limit generality. No estimated natural fault probabilities or calibrated combined uncertainty u_c/coverage k. No GUI/model/task/latency/token/power-loss/security-sandbox claim. Same-author separate audit is not external review.

## Timing and accounting endpoints
Total wall: perf_counter_ns before first fixture update/worker creation through last response AND all worker exits. First response: first report returned minus same sequence start, including initialization. Request latency: after fixture update through report return, including startup when needed, excluding subsequent worker shutdown. Child CPU: difference of RUSAGE_CHILDREN user+system seconds at sequence boundaries, converted to integer ns. Parent logging/audit after sequence end is excluded; interpreter/IPC/shutdown and fixture I/O inside sequence are included. Idle waiting, metadata bytes and source loading are not claimed absent. Pairing uses the same count and repetition; no trimming. nanoseconds converted to milliseconds by division by1,000,000. This is a validation-service endpoint, not end-to-end agent tempo.

## Conditional semantic argument
Each request runs the exact inspect_file function on the bytes present at its request boundary. That function reopens the file, reads and hashes the content, decodes JSON and creates a fresh deep-copied candidate for validation. For the declared immutable source, serial quiescent input files and no monkeypatch/concurrent caller, retained module constants do not contain previous verdicts or input bytes. Thus process lifetime alone does not change the function's inputs or control flow. Induction over the finite request list gives equal reports if each individual call returns normally; an invalid or missing file does not assert any later result. The empirical check verifies actual import/stdio/file/error composition rather than assuming this argument proves all Python behavior. No speed result follows analytically from this argument.

## Variables and unit check
| Symbol | Meaning (Japanese) | Unit | Definition | Domain / premise | Type |
|---|---|---|---|---|---|
| n | 逐次要求数 | 1 | fixed sequence length | 1,8,32 | integer scalar |
| j | 対応する反復番号 | 1 | technical paired repetition | 0..6 | integer scalar |
| T_f(n,j) | 新規起動方式の全経過時間 | s | end minus start, ns / 1e9 | positive observed value | scalar |
| T_r(n,j) | 常駐方式の全経過時間 | s | same endpoints | positive observed value | scalar |
| q(n,j) | 対応比 | 1 | T_r / T_f | positive | scalar |
| m(n) | 比の中央値 | 1 | median over seven j | finite technical samples | scalar |

The gate is m(8)<=0.50 and m(32)<=0.50. Seconds/seconds are dimensionless; CPU and elapsed wall are kept separate. For illustration only, 0.03s/0.24s=0.125; this is NOT a measurement.

## Roadmap / sources
Exact-source/ownership check -> construction and preserved first failure -> public freeze/readback -> three finite first-outcome batches -> raw audit/eight controls -> complete additive source/raw PR -> applicable exact-head CI/scoped review -> evidence integration/readback. Shared runtime defaults, #3850/#2 and global ROADMAP remain unchanged/open. No cleanup of dependent or foreign branches.
Primary implementation background: https://docs.python.org/3.13/using/cmdline.html (-I/-S); https://docs.python.org/3.13/library/subprocess.html (process/pipe/timeout lifecycle); https://docs.python.org/3.13/library/importlib.html (loading exact source). These document mechanisms, not this benchmark's result.
