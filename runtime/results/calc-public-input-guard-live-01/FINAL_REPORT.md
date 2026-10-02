# Explicit public input guard: fixed primary-use block terminal

Frozen candidate8b3dedf7c56963aa462a3314e5e20655ffd7c93a. Both original allocations
terminated exit0 without retries/repair/replacement or code/region/OCR tuning.
The successor uses owner.input_guard rather than assigning bridge.check,
backend.key_state or bridge.keyboard. Existing read-only app cue/source checks
remain trusted fixed-layout code; this is not generic perception or a sensor.

Normal: primary observes empty cells, enters731/864 through the shared graph,
then four public guard callbacks at sources12,13,14,15 permit one Ctrl+s. The
method returns SAFE_YIELD/effect_unavailable at the format modal with two completed
transitions, never TASK_SUCCEEDED. The primary reviews that exact original image,
acknowledges the focused modal once and reviews the main sheet. The post-Return
image still showed the dialog; it was not replayed. Original exec23164 terminated,
owned children disappeared, neutral release was verified. An independent read
then proves persisted731/864 with no other nonempty cells and matching source/
snapshot hash6ce839faeda1386b96cf14cede29b582a61d909db33d3a5e77158847d3ec40b5.

Wrong: primary observes731/863, unchanged goal731/864; graph returns SAFE_YIELD/
effect_failed with one transition before Save. No Save guard is armed/invoked,
no Save/format acknowledgement occurs. Original exec82582 terminates with neutral
release and owned-process cleanup. Independent persisted cells are empty and
source/snapshot hash3e0251add674da8426e574dde1cf1bc7d50813eff7c7b541d81e25affd681944
matches. This is a correct refusal, not successful completion of the goal.

| Case | Commands | Original primary PNGs | Physical/public captures | Programs / program emissions | Save | Local method reply |
|---|---:|---:|---:|---:|---:|---:|
| compiled-normal |16|7|21|4 /27|1|1.249427714s|
| compiled-wrong |11|4|11|2 /21|0|0.868395024s|

These are current counts, not copied from the previous recipe. The normal modal
returned an extra real image this time, unlike the prior destroyed-modal capture.
Single local intervals exclude startup/primary review and establish no matched
latency or human-tempo claim. Wrong-entry stopping is the graph/app cue gate;
live mutation between modifier and following key is not claimed here. Contract
controls separately exercise partial key input, freshness/lease/scope drift and
release. Owned children retain nonzero termination returncodes, not an all-zero
child-exit claim.

The candidate contract suites passed412 protocol+205 harness. Retained mechanics
and22 semantic mutation tests pass normal/-O, including all original checks and
new public guard source/stage/scope/timing checks. The file manifest and semantic
checks are separate. Frozen original recipe/runtime hashes remain unchanged.

Recommendation pending usage/publication: retain the explicit scoped Python
input dependency extension; keep defaults, efficiency gain and general-readiness
HOLD. It is trusted serialized synchronous code, not hostile-code isolation or
an interruptible I/O deadline. Capture-to-emission is non-atomic. No MCP endpoint,
automatic activation, scheduler, sensor or default perception was added. Actual
usage through this audit is pending, not zero. Full thread goal remains active.
