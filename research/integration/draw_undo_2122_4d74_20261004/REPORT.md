# D01 actual Draw Undo recording eligibility — negative first result

Base main61e704d63cb917ba5f03e2533c6e110e9daddb2f; Issue2122 remains open.
Two new disposable headless Draw documents, one producer invocation, zero retry.
This is construction eligibility, not the separately broader model recovery gate.

## Observed result

- insert_rectangle: after adding, visible history contained `Change object name of Rectangle to 'owned_rectangle'`. Actual Undo removed the name but left the rectangle at1000,1000 with size2000,1500. Frozen restoration gate against an empty page fails: FAIL_WRONG_RESTORATION.
- move_rectangle: initial shape setup under recording lock, later Position1000,1000→4000,3000 actually changed; no history entry/Undo availability. HOLD_OPERATION_NOT_RECORDED; no Undo attempted.
- Producer exit0/errors[] and soffice parent exit0; frozen auditor exit1/FAIL_OR_HOLD with `restoration:insert_rectangle`. All originals remain unchanged. Auditor independently parses FODG: first retains one rectangle at1cm,1cm; second retains one at4cm,3cm. Both2cm×1.5cm.

The insert source sets the name before capturing before_operation. The resulting history can appear when the shape is attached. The raw result does NOT establish that page.add records insertion, nor isolate a pure insertion-recording test. It demonstrates this exact staged sequence fails its restoration gate. The visible name-change description itself does not claim to undo insertion; no generic LibreOffice defect is inferred. This setup contamination is retained, not repaired/regraded. Direct Position has the separate qualified observation of mutation without recording in this route.

## Environment and custody

Existing Calc-only image lacks installed libreoffice-draw (dpkg status unknown ok not-installed). Separate public Debian build succeeded; image bab4dc0dff6ffa8270e86873c3987e0e3203c1b198a08ff971580a6c04c3ba1d, LibreOffice25.2.3.2 520(Build:2). Dockerfile/build logs/image ID retained. Public base tag is mutable at build time; output image is pinned for run, no claim of a pre-pinned base manifest. Source/plan/auditor frozen before producer.

Read-only source bind, network none, user65534, CPU1/memory512MiB requested. Actual sampled cgroups cpu.max100000100000/memory.max536870912/pids.maxmax. Swap warning retained. Root filesystem read-only and whole-host enforcement are not claimed. No GPU/provider/model/native GUI, user document, independent writer, authenticated footprint, concurrent authority or task benefit measured. Soffice parent terminal is not independent descendant reclamation proof.

## Integration decision and stop

HOLD_DRAW_COMPENSATION_ROUTE. Do not transfer Calc's setString Undo assumption to direct Draw Position/page.add. Existing recheck/SAVE_AS_NEW/ABORT remains the simpler candidate; its usefulness and current-generation authority still require actual verification. No runtime adapter or selective Undo subsystem is justified here. Stop this direct operation route. Any further UI dispatch or independently attributable writer study needs its own frozen successor allocation; D01 will not be replayed or regraded. Preserve421, CalcR01/R02 and modelM01 unchanged.

Issue result comment5974745151. Evidence delivery does not close2122, ROADMAP or the full research goal.
