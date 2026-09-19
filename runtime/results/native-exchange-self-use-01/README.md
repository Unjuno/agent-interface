# One-call native action, wait and image: Calc self-use

2026-09-20. The existing agent_exchange CLI now accepts --native to submit one
stage to the private Calc native harness, wait for its correlated report, and
return the existing native review image in the same call. It does not introduce
a new native backend, target policy or inferred task-effect detector.

## Actual primary-assistant use

The assistant viewed the initial source, then submitted stage 1 via this route.
The same call returned the action result and format-dialog PNG (sequence 7),
with no intervening process poll or separate review call. Local Python call
elapsed time was 1146.917 ms, including publication, waiting, report validation
and image packaging; it excludes outer shell/host delivery and model thinking.
The assistant visually confirmed 116 and 476 behind the dialog.

Stage 2 clicked Use Excel format with an intentionally zero wait budget. The
client returned pending with submission_committed=true, not an input-failure
claim. A later resume=true call read the same request's result and final sheet
(sequence 12) without republishing. That read took 66.118 ms locally; the frame
was already historical, so this is not a new action latency. The pending reply
is in the conversation but was not separately persisted; it is not included in
the manifest. Stage 3 explicitly finished and returned independent evaluation
[116,476] in 104.498 ms. A retained workbook reread confirms those values.

There are exactly two native program files, two completed action rows and three
hash-correlated replies. The resumed stage has no additional program. Every
program verified release. The existing modal-close BadWindow feedback remains
needs_review inside the report; explicit window review supplies the new image.
The response does not turn that earlier error into success.

## Scope and failures

Requests/replies are published as complete bytes using a same-directory hard
link with no overwrite. Duplicate submit refuses even for identical content.
Only explicit resume=true reads an already committed exact request. A mismatched
reply or changed source is rejected. Four native exchange tests plus nine old
exchange and nine review tests passed (22 total). No task input is retried.

This is a bounded single-owner research harness, not a production transport,
concurrent multi-client service, crash-restart deduplicator, or cross-session
recovery protocol. Preserve request slots and never reuse a run directory.
Filesystem reads/encoding can exceed the nominal wait timeout. Finished means
an explicit finish was evaluated; it does not claim cleanup has completed at
response publication. Cleanup is recorded separately and all tracked processes
are terminal. A missing server reply remains pending and must not trigger replay.

This demonstrates one fewer outer presentation/poll boundary on the normal
stage. It is not a matched task-speed or token-cost comparison. Primary-model
usage is unknown and helper-model calls are zero. Full responses are verbose;
compaction and a common promoted persistent entry point remain future work.

run/client-*.json preserves the actual returned metadata from the tool response
(base64 omitted; exact images are retained). Other run files are raw harness
artifacts. All 12 native image/hash links and the request/reply hashes were
checked. Source snapshots and 22-test log are retained. SHA256.json covers all
retained files except this README. Base aaedc064aba1cdc628e73ff04a6cdb91f42575ad.
