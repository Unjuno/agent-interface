# Issue #8665 T0 A01: observation load × cue information × response

This package constructs and independently audits a finite, deterministic 2×2×2 factorial. It separates an observation's event-loop/queue load from whether its same-sized, same-slot cue carries task-relevant information, then compares fixed replay with a response rule that reads only delivered cue codes.

The preregistration is in `PREREGISTRATION.json`. It is anchored to `main` at `23d1807ffad8359e0f89421ee2b9bf5783c9d5f4`; candidate and raw-only auditor source are frozen in the commit that contains this protocol. This T0 is CPU-only and uses the Python standard library. It does not run a GUI, model, OS input, container, network request, or shared runtime.

The first candidate invocation is intended to write 256 attempts: four preregistered regimes, eight matched seeds per regime, and all eight randomized cells per seed. Every cue payload has the same canonical byte length; informative and sham cues within a load level share the exact scheduled delivery time. Raw rows retain every observation, decision, action admission, verified release, effect receipt, deadline outcome, queue metric, and event trace.

The independent auditor reads only the preregistration and raw JSONL. It reconstructs all cells, order, timing, cue assignments, response decisions, releases, effects, deadlines, and contrasts; it then checks five corrupted copies. Candidate output is not itself evidence of live computer-control behavior. Even a method PASS describes only this synthetic finite model and does not establish an OS scheduling effect or a GUI result.

Before the first invocation, preserve the source freeze and command identity. Retain the first PASS, FAIL, HOLD, or STOP. Do not overwrite or rerun the candidate after an outcome; any auditor-only correction must preserve the original raw and use a versioned successor.
