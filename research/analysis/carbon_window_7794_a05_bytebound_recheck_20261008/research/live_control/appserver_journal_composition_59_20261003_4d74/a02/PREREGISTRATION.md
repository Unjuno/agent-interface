# Request-journal deadline composition preregistration

Owner Issue #59; coordination #6957. Owner task 01a0b98a-4d74-7552-9505-25cd77cc99e6. Allocation APPSERVER-JOURNAL-MUTEX-COMPOSITION-59-4D74-20261003-A02. This is a directed ordinary subprocess/mutex integration experiment, not a replay of any native author's finite allocation.

## H / T / D / C / U

H: Literal bounded-send (#6965) and bounded-close (#6955) composition atop current-main no-drain EOF still blocks a request in _record('sent') when the journal mutex is held. A sent-journal mutex deadline comparison refuses before the fixed checkpoint and emits no peer bytes.

T: Six sequential real Linux Popen echo-peer cells: main, composed, bounded_journal × healthy, held_journal. Every call requests timeout0.05s. In held_journal, lock acquisition is confirmed before caller start; hold persists through0.25s observation and releases no earlier0.40s after caller start. Each cell has a6s external watchdog. Retain timestamps, request result/error, exact child-observed wire bytes, journals, source hashes before/after, and process/thread/pipe/journal endpoints. One producer invocation, then one independently implemented saved-output auditor on exit0; retries0. Construction validates source AST custody/configuration without running these cells. Candidate staging contains source and protocol fixture only.

D: Each healthy row must echo exact within0.25s. Held main returns only after release; held composed remains blocked at checkpoint, then raises the pre-send budget TimeoutError with zero peer-observed bytes; bounded_journal times out before checkpoint with0 peer bytes. Saved-data audit must independently join all6 cells, source identities, event ordering, peer bytes and cleanup and reject5 copied corruptions. A fixture/provenance failure is STOP, not a favorable result; a valid contrary observation remains FAIL/UNCERTAIN. Any first output is immutable and no candidate retry is permitted. OS write-syscall entry is not instrumented; code-path inference is separate from peer-observed byte evidence.

C: Directed mutex contention, small controlled regular-file journal, one finite Linux sample, scheduling tolerance250ms compared with50ms request budget. Timings describe this fixture; they are not latency distributions or worst-case OS bounds.

U: Only sent-journal mutex acquisition is changed in the comparison. Journal write/flush, serialization, condition acquisition, arbitrary predicates, descendant retirement and external effects remain outside the bound. No whole-call hard deadline, server/model readiness, Windows compatibility, GPU, GUI, game, OS input, physical release, independently useful feedback, token-efficiency, human-tempo or #59/#57/roadmap completion claim. Existing send/close/EOF/UTF8/reader/Boolean-ID owners retain their scopes; no public runtime source is modified or adopted.

## Source and runtime custody

Current-main source snapshot66822a57d2bc05082c6b82aa0b02bf7762dba98b; client Git blob6e34f7c17300072e6739ded5e3f977974c2673be. At claim time, fresh mainc79f1ef958f46ff6f146edf6f3065826463ade01 has the same client bytes. Send proposal atfbd804e549b589e7e7e692ab4f89183d21451ca7 / blob5f408d10850f69db3bd1279c5018044120d9a2df; close proposal at31f10e660d2e7e13d8fe05c9a56d3f3c5e71f324 / blobb1d4762ae4d3ccef8c4dd73198c01b247a2c07e7. Literal scoped deltas retain the current no-drain EOF AST; copying either full old proposal would regress it. Construction must verify this composition.

Installed WSLc3.0.1.0, Linux/amd64 Python3.12.14, cached image IDsha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4 and repo digestpython@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f. Pull never; network none; user65534:65534; source readonly; distinct fresh writable output; .25CPU/512m requested. Preserve engine cgroup/swap warnings; configuration alone does not prove enforcement.

Before any invocation: publish all frozen source/config/audit/commands/hashes in a draft PR; confirm source heads/local bytes, current main and no client/path overlap, relevant owner/branch claims, known empty overlapping WSLc inventory, exact image ID/digest and absent formal outputs. Construction precedes candidate; failures STOP before candidate. No shared Docker daemon or GPU lease is used.

## Prospective control-only successor A02

Claim https://github.com/Unjuno/agent-interface/issues/59#issuecomment-5967943399 precedes execution. A01 freeze305c032829b880c4fd8018e712a98b2176a336b0 / PR6994 first producer STOPped all6 on350ms peer readiness before any caller began. A01 raw/partial outcomes stay unchanged and are not pooled. A02 changes setup readiness to2s, setup rendezvous to1s, and per-cell watchdog to6s, explicitly consumed from fixture. The50ms request/250ms checkpoint/400ms fixed release, six cell order, clients, image, requested CPU/memory and method rules are unchanged. This is a new versioned setup allocation, not a replay or regrading of A01. CPU quota versus host mount IO contribution remains uncertain; the setup change isolates neither cause. First A02 result is retained; no further timing tuning within A02.
