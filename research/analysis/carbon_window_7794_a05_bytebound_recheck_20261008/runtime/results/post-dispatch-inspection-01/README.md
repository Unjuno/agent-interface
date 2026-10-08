# Optional post-dispatch inspection: integration evidence

Issue #5256 adds opt-in `inspect_after` to persistent X11 dispatch. It reuses existing metadata inspection after completed, released input. It neither captures another image nor selects a target; the agent still reviews and explicitly selects a changed target. Failed inspection keeps the completed action receipt. Summary preserves complete successful inspection; errors and skipped inspection fall back to full.

## Primary use

- Calc on implementation build `10b88f2eb`: one fresh allocation (seed 991401), seven MCP calls, three input programs, six reviewed captures. Bundled Save inspection identified Confirm File Format; the primary explicitly reviewed that candidate without a separate pre-modal inspection. Independent XLSX scoring verified A1=862 and A2=506. This early build used full fallback for enriched dispatches. Return plus 100ms still captured the dialog; later read-only inspection showed the sheet. No replay.
- The first two-editor allocation was interrupted by the user-authorized WSL restart before any primary MCP request. Its allocation remains archived and is not called a completed trial.
- Child-target trial on build `f91430ca8`: five calls, two completed input programs and one refused invalid program. Left saved `http://p_q`, Right received no audited events. Deliberate Right inspection failed after completed Left input. The caller then used unsupported `key` operations; validation refused the save before execution and inspection was skipped. A corrected `key_chord` saved successfully without retyping. Left inspection also failed: the configured Tk child is not its managed client.
- Fresh read-only diagnosis records the child-to-managed-window ancestry and both inspection results. A child ID fails the existing transient-family contract; its managed ancestor succeeds. This is a configuration limitation, not fixed by this feature.
- Managed-target trial on the same build: four calls, two completed input programs, three reviewed images. Deliberate Right inspection failed while preserving completed Left input. The next save returned the successful full inspection context inside a summary. The primary observed `saved:http://p_q`; independent scoring confirmed the exact value, and Right has neither an effect file nor audited events. No rebind, input replay or helper model.

The fixture for the last trial resolves and records the actual managed ancestor before allocation. It does not silently reinterpret targets inside production. Use managed client IDs for target inspection; arbitrary child/widget IDs that work for input are not interchangeable with managed family roots.

## Evidence and limits

`raw.tar.gz` contains 174 hashed files: all four allocations, delivered requests/replies, image review receipts, independent saved effects, terminal cleanup statuses, source fixtures, two portable builds, two native suite results/logs, metadata diagnosis, and offline summary projections. Primary action decisions were made from returned images; the verifier checks recorded identities and effects rather than interpreting pixels or proving attention.

Calc's seven calls versus the earlier eight-call example use different values/builds and are not a controlled speed comparison. The offline summary projection compares the same retained responses and is labelled offline. Host timings are orchestration boundaries, not model ingestion, useful-feedback or semantic-completion latency. No measured model-token, fee, human-tempo or general speedup claim is made. Failure allocations and caller mistakes remain part of the result.

Run `python3 -O runtime/results/post-dispatch-inspection-01/verify.py`. It verifies member hashes, exact call sequences, saved worksheet values, one text emission in passive event logs, untouched Right, preserved input result on inspection failure, invalid-program skip, successful summary context equality against the stored report, post-dispatch timestamp ordering, explicit modal selection from the bundled candidate, image-review bindings, native log hashes and terminal children. It does not rerun GUI input.
