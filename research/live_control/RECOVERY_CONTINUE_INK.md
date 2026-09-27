# Model continues editing after recovered intermediate result

A fresh Inkscape seed239 fixture scripts the intermediate X88 edit/save and deliberately abandons its response. The append-backed caller retains pending identity, refuses new input, and performs one command-free recovery read. The final task is now X104,Y50,W40,H30, so the intermediate completion cannot satisfy the task. The same recovery view is sent directly to the constrained Luna-low responder.

The model chooses pointer click(549,106), Ctrl+A, text104, Tab, Ctrl+S. This proposal is validated against the existing bounded numeric action subset and executed unchanged after a fresh observation and matching focus/binding check, with a new clock/deadline and unique action identity. An observe step is appended by the runtime harness. The model then receives the new action's returned view/current screenshot and requests independent verification. Saved SVG independently contains x104,y50,width40,height30 without a transform. The original X88 request is echoed once; the later X104 request has a distinct ID. There are two Save chords for two distinct edits, not replay of the lost command.

| Measurement | Observed |
|---|---:|
|Loss to original read resolution|0.959s|
|Model new-edit runner|10.552s|
|Fresh checks plus action result after model return|1.178s|
|New action request/result round trip|0.858s|
|Model verification runner|7.150s|
|Initial capture to independent evaluation|21.250s|
|Model input / cached input / output|21104 / 8704 /355 tokens|

These are one episode's component measurements, not a matched speedup, model-serving latency estimate or human-parity result. Windows runner times and Linux runtime intervals are calculated within their own clock domains. Model decision time remains dominant. No provider monetary cost or actual serving identity is available.

The audit checks90 events,16 exact decoded frame/PNG pairs,17 append records and all source/model/proposal/image hashes. It replays all received slices and journal state; verifies original request attribution, recovery view, fresh observation sequence/binding and clock/deadline, unchanged proposed steps plus explicit observe, distinct edit IDs, four admitted/released programs (selection, old edit, fresh observe, new edit), and the independent SVG. The assistant viewed the final screenshot with X104. Driver exits0, private sockets removed and no error artifact. Raw evidence is results/recovery-continue-ink-01. Run audit_recovery_continue_ink_v1.py under Linux for evidence replay without model or GUI execution.

Scope: the intermediate edit is scripted, while the post-recovery edit and final visual verdict are actual model choices. The driver supports one act then verify and stops otherwise; this is not a general multi-step planner. Initial JSON decoding precedes action revalidation and is not a duplicate-key refusal contract for arbitrary raw responses. Numeric final verification excludes bool but is task-specific. Fresh focus/binding checks do not establish unchanged semantic targets, and this successful trace does not prove resistance to target movement during model inference. Research failure cleanup and journal limits remain as documented.

Decision: the returned recovery result now supports a genuinely new model-selected action, beyond verification-only use. The next important uncertainty is changed targets between model observation and execution: exercise a controlled target/focus change in this post-recovery path and verify refusal without replay, using the existing sampled-target/focus machinery where applicable. Do not create further identical successful X-coordinate traces to imply broad desktop coverage. Input correctness under live changes and human-tempo remain open requirements.
