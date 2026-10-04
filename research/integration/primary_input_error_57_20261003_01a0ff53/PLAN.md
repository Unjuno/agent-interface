# Input-error ownership boundary (#57)

H: the existing sequential primary stream can retain an accepted command's result or uncertainty when Readline forwards a source read error, using the existing failure/close/pending-observation path. The baseline listener catches errors on the input stream but omits the separate Interface error.

T: ordinary native Node26.7.0 engineering, two exact source arms × four event schedules = eight children, in fixed baseline/candidate order. Scenarios: input error before any request; input error while an inert successful request is pending; input error while an inert failing request is pending; EOF while a successful request is pending. Barriers use event-loop turns and an explicit promise release, not time estimates. One comparison process, one standalone raw-only audit; caps1/1 and zero retries after this freeze. Each child timeout5s, outer30s, total stdout/stderr/raw limit1MiB. No previous allocation/probe is repeated.

D: scoped PASS requires all eight rows reconstructed, baseline unhandled Interface failures retained, candidate error outcomes observed after the same pending promise, exact success/uncertainty responses, zero replay, no request before admission, both EOF positives preserved, actual exit codes and all eight effective corruptions rejected. Any unexpected event order, timeout/missing row, changed source or mismatched audit is FAIL/HOLD and remains the first outcome.

C: this is standard EventEmitter error handling. No new cancellation mechanism, serializer or byte policy is needed. An output failure or a pending exchange that never completes still has its existing limitations. Pending output may be unavailable for other reasons; this study uses a responsive sink.

U: actual Node streams and an inert exchange, not a native backend, relay process, physical task effect/release, clock trust, performance, production concurrency or hard I/O deadline. Direct stream-owner rejection is tested; actual CLI cleanup follows existing runPrimaryStdio code and is not claimed as a newly executed relay effect. Equal callback and source listener paths converge on the original first error. Node22/24, Windows and real pipe/device fault injection are not executed here.

The production repair is one Interface error listener; two regressions are added to the original stdio module already selected by native-mcp-v1 workflow. No workflow/triggers/schema/default change. PR6902's busy-response guard remains its author's separate immutable delivery; later composition requires an exact source check.

Primary guidance: [Node Readline error event](https://nodejs.org/api/readline.html#event-error) and [Stream implementer callback contract](https://nodejs.org/api/stream.html#implementing-a-writable-stream). These docs are reference guidance; actual behavior is established by the pinned installed Node binary and retained child outputs, not the documentation's current version number.
