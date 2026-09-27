# #1465 T2 raw receive-return linearization successor

BASE: c2826ec7cfb2aceaf55c9ef0e6fe1e9ed301692c
TASK: CONCURRENT-FAST-DECISION-T2-RAW-RECEIVE-LINEARIZATION-A10-20260918-013
Parent: #1376. Direct predecessor: #1449 / PR #1452, formal0.

One factor only: frontier-return observation/authority linearization.

Predecessor: blocking recv() completes before authority lock acquisition.
Candidate: authority lock -> poll(0) -> if readable recv() -> raw receive-return timestamp -> close generation -> release lock. The lock is released immediately when poll(0) is false; it is never held while waiting for frontier readiness.

H: placing actual userspace recv return and generation closure in one authority critical section prevents any admitted local commit after raw receive return while preserving valid pre-return CLEAR admissions.

T: standard-library multiprocessing.Pipe + threads + perf_counter_ns. Excluded construction includes a forced 2ms post-recv window in both modes: outside lock for predecessor, inside lock for candidate. Candidate cases use four #1449 state programs. Bounded nonformal stress follows only after construction eligibility. Formal is not run without an exact-head #60 grant.

D: predecessor must expose >=1 admitted raw-receive-gap violation; candidate violations0; boundary probe prepared pre-return and attempted post-return must reject; selector exact; HARD yields; useful pre-return ADVANCE remains where CLEAR exists; terminal generation=2/closed; child/thread cleanup exact; independent audit/corruption controls pass.

C: result is about Python authority semantics, not production ABI. Poll cadence may add latency/contention. Boundary is actual userspace recv return, not kernel arrival. Receipt drain is separately owned by #1459.

U: no model/provider/network/GUI/X11/task input/shared runtime. No provider latency, task usefulness, physical-actuation or human-tempo claim.
