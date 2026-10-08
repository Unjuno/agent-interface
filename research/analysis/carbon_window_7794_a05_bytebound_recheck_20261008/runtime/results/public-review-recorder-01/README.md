# Public capture review attribution in the host timeline

The instrumented relay client's review method previously accepted only reports
with guarded/native source.sequence and source.observation_id. Ordinary public
MCP use therefore kept hand-written reply-bound review notes outside that method.
The recorder now also accepts public observe/dispatch image references and
management observation_report images. It emits a distinct v2 public-capture
receipt, retaining exact reply and image hashes, capture timestamps, configured
target and coordinate frame. Public source_sequence is null; no sequence is
invented from a caller assertion or relay ID. Dispatch observation_id can be null.

Public acceptance requires one delivered image whose byte hash equals the
artifact hash and complete capture identity. Missing/ambiguous/unknown or
mismatching evidence refuses without creating a receipt. Existing guarded/native
v1 receipts remain unchanged. The same host review_recorded event links the new
receipt by reply hash; this is caller-declared review attribution, not proof of
attention, semantic completion, first useful feedback or model-thinking duration.

Validation: 15 Node tests pass, including a public capture through the instrumented
host's send/present/review sequence and unchanged uncertainty/no-replay behavior.
An offline pass over all eight retained Calc replies accepted the five replies
containing images and rejected the three without images. The five generated
receipts explicitly say retrospective-recorder-check; they are not new live
primary decisions and must not be used as timing measurements of the earlier task.
Original live review notes and frozen Calc evidence are unchanged.

Initial Windows Node CLI attempts could not resolve the UNC test-file paths
(the first two-path call also appeared as a combined path). No test executed
in those attempts. Tests were then run with the existing WSL Node installation:
14/14 passed before the host-specific test was added, then the final 15/15 passed.
This is an invocation correction, not a candidate test failure or hidden rerun.

The archive retains implementation/tests, both Node logs, the offline driver,
its result and five new attribution receipts. The manifest pins source. Run
`python3 -O runtime/results/public-review-recorder-01/verify.py` for read-only
verification against the earlier Calc archive. No GUI, model call, input,
image compression or task-performance experiment was run for this change.

Use this method on future actual public image reviews after presentation to keep
transport, delivery and caller review boundaries in one host clock timeline.
Callback completion still does not establish host-render or first-useful time.
