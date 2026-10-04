# #5260 A07 — focus-receipt instrumentation perturbation successor

H: Synchronous file publication inside a Tk focus callback can change the
observed click->FocusIn->first-key ordering relative to memory-only receipt
recording. A shared instrumented app in every arm is not an uninstrumented
baseline. A05 and A06 motivate this question but do not establish its cause.

T: Planned fresh8-app construction: MEMORY_ONLY/SYNC_FILE x idle/cpu_busy
x2replicates. Immediate XTest hxy after one target click,20ms gaps, oneSave
250ms after lastkey; no ackwait/automaticreplay. Same app/code/geometry/
ReadinessOnce/pinned image/privateXvfb, treatment only focus-file I/O.
All focus events recorded in memory in both arms; actual per-file write/
flush/fsync/replace start/end retained for SYNC_FILE. Memory receipt data
is copied, not a mutable alias. Candidate once/eightapps, separate raw/file
auditor once/no retries. Old A02/A03/A04/A05/A06 never replayed or edited.

D: complete source/fixture/image/first streams/input/app/readiness/event/
file trace and clean child exit gates -> METHOD_PASS_CONSTRUCTION_ONLY.
Exact-save/decoy-first-key and focus-callback intervals are finite arm
observations. No population causal or instrumentation-free inference from
8apps. Missing/broken custody -> first STOP, no consumed source repair.
No H-efficacy threshold is changed after seeing outcomes.

C: dedicated new additive path/branch, same cachedWSLc image217851fe68e7,
networknone/source+inputRO/uid65534/requestCPU0.5/512M capunproven; own
privateXvfb only, no sharedphysicaldisplay/model/GPU/config changes.

U: Recording focus events itself also has overhead in MEMORY_ONLY. File
I/O may perturb scheduling even when a character is not lost. This is not
A05row009 attribution, a public focus sensor/defaultwait fix, Docker/WSLc
speed or resource-benefit measurement. Avoid treating observed callback
receipt time as an uninstrumented event-arrival time.

Both arms retain record-entry -> completed-record clocks. This interval excludes
the final returned deepcopy, caller append and full Tk callback return; it is
not an OS event-arrival/physical-input latency. SYNC_FILE intervals include
hash/stat after replace. Busy process must cover the entire click-start ->
first-key-sync-return phase and its recorded duration must be >=2200ms.
All8 rows require three app KeyPress events and one Save plus their exact
requests, copied readiness, first-visual file/frame custody and clean app/
private-display cleanup. Visual task correctness is not inferred from hashes.

Roadmap: TDD memory-vs-file recorder with copied snapshots and write traces
-> derive fresh app/candidate/independent audit -> freeze8app source/fixture/
argv and CPU use -> execute once -> retain outcome/readonly adversaries ->
batchPR/main. No A07 container/input has been invoked; preparation only.
