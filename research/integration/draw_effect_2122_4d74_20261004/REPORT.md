# E01 wait discriminator: delay is not a remedy

New diagnostic allocation under2122; old L01/D01/421 unchanged. Source base9c3a6b8a761e460baa6a3c8c801c93a34f3b7252. Eight NEW disposable Draw documents, frozen wait order0/9/9/0/9/0/0/9seconds, no model calls, no setter retry.

## First observed data

Each actual independent writer sets A1700 and B2700 while undo manager locked. Fresh source/admission checks agree. All logged actual setter arguments are1900,1000.

|wait condition|immediate task success|saved task success|protected B|
|---|---|---|---|
|0seconds|4/4|4/4|4/4 preserved2700|
|9seconds|3/4|3/4|4/4 preserved2700|

`wait_9_1__fresh_read_reference` fails: immediate,100ms,1s andsavedFODG all retainA1700,1000 despite target1900,1000; size500×500 andB2700 retained. Actual wait9.000127107seconds. This is an actual incomplete task, not a mere missing read or model output. Parent/producer0/errors[]. Original saved XML audit0/errors[] validates retained data, not task correctness; one failed endpoint remains.

Frozen auditor decision is **HOLD_NOT_REPRODUCED** because its first conditional tests whether the0-second arm exposes an immediate failure. This label means no original immediate-arm failure in this new finite schedule, NOT that the application mismatch was absent: the delayed arm exposes one. Do not reuse that label without the matrix. The9-second wait is not sufficient to eliminate the observed mismatch. There is no causal claim that delay causes failure or that waiting is generally harmful; fixed sequence, shared office process, instrumentation and small directed denominator cannot establish such a rate.

The parent script records APPLIED/input_mutations as one setter invocation only, not verified task completion, as already disclosed in L01. Subsequent reads are observational, no repair/retry. Additional instrumentation and later saves differ from oldL01, so E01 is not an exact reproduction/reclassification of it. Delayed failure remains incomplete through1second after invocation and in saved content; no later eventual state is measured.

## Scope and decision

**HOLD_INTERNAL_CAUSE / DO_NOT_ADOPT_WAIT_REMEDY.** The hypothesis that a roughly model-sized9second idle interval is sufficient to resolve the prior mismatch is contradicted by this directed case. The internals causing it remain unknown. Do not infer that a model is necessary from L01's4/4 versusreference3/4 or add artificial sleeps to a runtime on this evidence. Stop expanding wait schedules and model prompts. Next work needs actual application/source mechanism evidence or a qualified independent effect acknowledgment, not a setter-return completion flag. No root-cause fix has been made or claimed.

Imagebab4dc0dff6ffa8270e86873c3987e0e3203c1b198a08ff971580a6c04c3ba1d/LO25.2.3.2. L01 source andraw copied byte-exact for provenance, never executed as original actors. E01 source/plan/auditor/writer/sourcecopies frozen before run. Source bindreadonly/networknone/user65534; cpu.max100000100000/memory.max536870912/pids.maxmax sampled, swapwarning retained. NoGUI/userdocument/provider/GPU/authenticatedexternalownership, naturalconcurrency, atomicrevision/ABA/futurewriter or task-valueclaim. Full2122/ROADMAP remainopen.
