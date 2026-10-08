# Excluded construction history

Original test-first methods: RED 4tests, 1failure+1error (the missing transport
showed a TimeoutError rather than RuntimeError). RED-v2 made that discrepancy a
typed assertion: 2failures/0errors. Both first streams preserved, not relabelled.
First generator/GREEN failed literal-boundary preflight: pinned file has LF
function sites with a final historical CRLF blank, and wait's observation branch
uses two lines, not one. Generator corrected its literal sites; every other byte
and final CRLF remain identical by inverse check. GREEN-v2 4methods PASS.
Expanded methods use actual candidate parser/decoder/queue/wait and preserve
monitor priority. Saved-audit producer_pid=True mutation initially accepted as1
(RED), now exact-int rejects it; five semantic receipt mutations are tested.
No method test is the native six-cell allocation. Fixtures are generated saved
receipts, not actual thread/child evidence. Full application suites/game not run.
Cleanup helper is mechanically AST-extracted from reviewed E01 source SHA256
3db505015d7ea917e66447f9057dce2504a6d2a746abaa6b033b595ea2dc5982;
no E01 allocation/executor replay. Candidate source snapshots remain inert.

Independent reviewer prelaunch HOLD exposed actual EOF not closed by standard
stdout wrapper, last-cell child_alive omission, and incomplete metadata/handshake
gates. Actual EOF peer-only helper test failed (RED) before os.close(1), then
passed; it never executes candidate reader/wait and is excluded native allocation.
Producer completion now includes child_alive; parent wait/CONTINUE and emitter
write start/return timestamps retained. Auditor checks metadata and ordering.
Nine methods now cover seven semantic receipt controls (five typed custody,
missing allocation count and invalid handshake). Cleanup absent-stream lookup is
a retained defensive limitation: actual PIPE construction always supplies handles;
we do not promote this helper to general subprocess lifecycle coverage.
