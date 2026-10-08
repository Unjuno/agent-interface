# Windows6501 T02: stale cancellation after directed native worker reuse

Scope claim6501 comment5970770590; author6178 / FINAL-v5. This is a NEW four-cell once-only allocation, not T01 replay or portable/runtime qualification. Intake4dc7fa83e6146439144e7c46240a40e8c7ca1b1b, own native Windows11/CPython3.12.14/stdllib. No shared GUI/input/model/GPU/VM/network/install, native thread belongs exclusively to this child.

H: after one owned worker completes readA and begins readB, an old still-valid thread handle can cancel B; a generation check detached from the eventual native call can also authorize that stale request. A standard current-generation check under the same lock used for worker admission refuses stale A in this directed B-pending schedule. No OS queue atomicity/general pooled adapter guarantee is proposed.

T: finite model first enumerates check/switch/nativecall order (check precedes call), contrasting released check versus lock held across check/call and worker admission. Then native empirical residual: ordered normal_B_D, stale_handle, check_then_call, locked_gate, each one fresh child with two separate own anonymous pipes and the SAME workerTID for both sequential native ReadFile calls. A must have three native successful pending observations before normal D44 delivery. For check_then_call only, generation1 precheck before A completes. A read returns exact44; worker then admits generation2 under ownership lock and starts B. Three B pending witnesses, no B data, precede requested cancellation for generation1. Normal positive writes B=D; unsafe policies call CancelSynchronousIo on the retained A thread handle. Locked gate refuses before any native cancellation while B is active, then separately labelled D cleanup. Every original outcome retained.

D: METHOD_PASS_SCOPED requires complete source/dependency/raw/supervisor/resource joins and all four rows. H expected: A normal44 in everyrow; normalB44 primary; stale_handle/check_then_call actualB FALSE/error995/count0/empty and primarydone; locked_gate stale request refused/no nativecancel/B unfinished throughout500ms before separatecleanup44. Contrary well-formed data means H_FAIL or UNCERTAIN, never row deletion/retry. Missing three witnesses, source mismatch, child timeout, incomplete join/resource cleanup means STOP_INFRASTRUCTURE; halt remainingcells. One primary producer child per row, one frozen raw-only auditor; ordinary model/parser construction and separately versioned saved-data repairs are distinct. API success alone is not I/O completion. Read-return may precede native-cancel-return; equal clock stamps give no latency estimate.

C: directed schedules exaggerate risk and do not estimate natural frequency. An exclusively owned one-shot thread already avoids this reuse boundary. A local generation gate is insufficient if another dispatcher does not use the admission lock, if OS handles are reused independently, or if cancellation precedes I/O queueing. This assay deliberately holds A's actual thread HANDLE open until both reads finish; it does not test stale integer HANDLE reuse. `check_then_call` releases the check lock before A→B, exposing its documented gap. No new cancellation invention or runtime adoption is needed to retain a counterexample.

U: four synthetic conditions, one observation each, no population statistics, efficiency/latency/arbitrary driver I/O/file-specific atomicity/task-effect/authority/recovery deadline/physical input release/portable guarantee. GetThreadIOPendingFlag samples thread state; ownedbarriers/generation/pipe provenance associate observations here, not general OS operation authentication. Any missing original timestamps/PIDs are UNKNOWN rather than invented.

Budgets: primary500ms, admission/join2s each, outer10s per child, all output<=1MiB. One worker per child, main thread uses5ms polling; no stress/load loop. Emergency D writes are cleanup only. Native cancellation is attempted only on owned thread after exact B witnesses. Own threadHANDLE CloseHandle then CRT FD EBADF evidence required. No CancelIoEx/TerminateThread/process-wide cancellation.

Primary sources: Microsoft [CancelSynchronousIo](https://learn.microsoft.com/en-us/windows/win32/api/ioapiset/nf-ioapiset-cancelsynchronousio) and [cancellation considerations](https://learn.microsoft.com/en-us/windows/win32/fileio/canceling-pending-i-o-operations): completion status must be observed; subsequent calls on a reused thread can receive cancellation. Those contracts are motivation, not this host's measurement.

|Symbol|Japanese meaning|SI unit|Range/assumption|Type|
|---|---|---|---|---|
|A,B|同一ワーカー上の前後二つの読取|1|別の専用パイプ、各1byte|operation identifiers|
|g|現在の操作世代|1|A=1,B=2; ownership lock protects admission|integer scalar|
|t|観測時刻|ns|host monotonic clock, equal timestamps permitted|integer scalar|
|w|一次観測窓|s|0.5, cleanup excluded|real scalar|
|n|実際の読取byte数|byte|0 or1, DWORD from ReadFile|integer scalar|
