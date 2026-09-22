# #4124 Parent-death ownership channel

H: A worker-side read end of a manager-owned pipe can make manager lifetime explicit: normal exit, SIGKILL, and explicit close produce EOF and bounded worker-local helper cleanup; a distinct client disconnect does not.

T: Standard-library Linux process experiment. Two policies (NO_PARENT_DEATH_CHANNEL, OWNERSHIP_PIPE) × four events (manager normal exit, manager SIGKILL, explicit cancel, client disconnect) × two repetitions = 16 fresh cases, split into two immutable 8-case batches. A separate-session sentinel is outside the owned set. Scored observation precedes common rescue. Construction is excluded. No retry/replacement/pooling.

D: PASS_PARENT_DEATH_OWNERSHIP_CHANNEL_SCOPED only if all 16 cases reconcile; baseline worker+helper remain live at score; candidate parent death and explicit cancel emit cleanup receipt and leave worker/helper non-live; client disconnect leaves them live; sentinel survives every score; final common rescue leaves no process residue; raw-only audit and >=10 mutation controls pass.

C: Cooperative worker, one enumerated non-daemonizing helper, correct FD inheritance, Linux pipe EOF semantics. Common rescue is not credited to candidate.

U: No actual MCP server/runtime path, GUI/input, arbitrary descendants, worker death, PID-reuse stress, uninterruptible sleep, physical release, model/task/token/latency/product claim.
