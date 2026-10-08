# Bounded append checkpoint candidate: recovery retained, short-session cost lower

append_checkpoint_v1 stores canonical JSON frames containing version,index,previous digest,full state and SHA256. durable_submit_v4 keeps v3 command/clock/reconciliation behavior and cooperating-process flock, replacing only checkpoint store/load. First creation fsyncs the file and its directory. Later pre-send and post-reply commits append and fsync the existing file, avoiding per-commit file replacement/directory sync. No fsync is removed from the pre-send uncertainty commit. Initialization remains explicit and refuses an existing journal.

The loader validates every frame's sequence/hash chain and refuses empty, malformed, oversized, torn or corrupt files. It does not drop a partial tail or silently return a previous state. Bounds are256 records,1MiB per frame and16MiB total, with no automatic reset/compaction. It assumes a trusted local file and cooperating single writer; hashes are damage detection, not authentication, and cannot detect replacement/truncation to an earlier complete valid journal. Power loss and filesystem rollback remain unproven.

## Recovery evidence before timing

probe_append_checkpoint_v1/results/append-checkpoint-01: partial tail, invalid JSON, repeated frame and changed payload all refuse before transport and preserve bytes. Injected fsync failure during the pre-send commit propagates before transport; a complete pending frame remains readable and the next command is blocked. This tests process-visible uncertainty, not physical durability after failed sync. At256 records the next append refuses without changing bytes. Zero transport calls in these controls. Corrupt journals currently block reads through this wrapper too; no automatic salvage or independent runtime reconciliation UI is implemented.

probe_append_replan_v1/results/append-replan-01 repeats the integrated actual Inkscape path with the append backend, seed237. A real expired submit is sent and its caller exits17 before recv; another worker is refused before transport; a third reads its attributed rejection. Journal-owned clockÅ®fresh observeÅ®clockÅ®distinct X104/save follows on the same live runtime. Audit checks11 append frames,62 runtime events,10 exact image frames, three worker PIDs, one rejected request with zero started steps, three completed/released programs, own clock/sequence/deadline associations, SVG104,50,40,30/no transform, and final exit0/socket cleanup. This scripted path tests process loss on a rejected request and subsequent real edit; it does not add a new lost-response-during-accepted-edit test or autonomous model planning result.

## Fixed native-filesystem comparison

probe_append_cost_v1/results/append-cost-01 uses replace/append/append/replace, four fresh Inkscape sessions with four clockÅ®observe cycles each, seed236. Both journals reside in private native Linux /tmp directories during measurement. Output/runtime files remain in the repository for both arms. Initial startup/capture/journal creation, finish and result copying are excluded. The previous timer harness and full event/continuation/frame/SVG audit are retained. Both paths assign identities inside their API timers. The driver retains an inherited received/durable module docstring; plan.json and selected replace/append callables define the actual experiment.

| checkpoint | operation | total median ms | outside-transport median ms |
|---|---|---:|---:|
| replace | clock |50.264|31.005|
| append | clock |35.381|17.444|
| replace | observe submit |118.346|31.134|
| append | observe submit |99.976|18.176|

Eight-call measured session totals: replace703.635/646.241ms; append540.985/543.930ms. Each session has36 events,five exactly reconstructed frames,four completed/released observation programs and unchanged SVG50,50,40,30. All32 measured calls pass exact reply/continuation/source/clock audits. Append arms finish with17 records; temporary journals are copied after timing then cleaned up. This is a descriptive improvement on a short static observation workload with two sessions per mode, not a population estimate, equal power-loss guarantee or general agent speed claim. Transport varied too; outside-transport residual includes chain scanning, JSON, locking, synchronization and bookkeeping, not fsync alone.

The full-state log grows and is rescanned on every load/append. Long-session overhead, compaction, record-limit recovery and storage exhaustion are unresolved; the256-record ceiling is a real operating limit. Caller loss after writing a complete frame, truncation at a complete-frame boundary, actual power interruption and non-cooperating clients are distinct failure cases. This remains a candidate, not the default caller or production restart-storage policy.

Next use this candidate in an actual model-facing decision loop, measuring model input and decision-to-observation waiting while preserving received evidence. Prefer a new task/domain over another identical Inkscape edit. Carry the measured17-record regime and unresolved long-session limit into that choice. Do not spend further turns on isolated recovery variants unless real caller use requires them.
