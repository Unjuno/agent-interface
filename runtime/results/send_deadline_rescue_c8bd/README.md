# Send-deadline rescue intake and composition boundary

Original PR #6965, source `c8bdf4de32f5f09146ce295ab0629dc3e40fc62b`.
V1/V2/V3 inert evidence packages are restored unchanged. Original science,
RED/GREEN, publication/construction failures and withdrawn V2 adoption remain.
No active client/test/runner file has been copied from the old branch.

Fresh comparison against main `e14246bcb` identifies incompatible wholesale
application: original branch would remove explicit UTF-8 Popen decoding,
Boolean reply-ID rejection, reader-alive timeout and bounded journal-lock close.
Its native-suite image would remove existing reader/journal, reply-ID and UTF-8
registrations. Those main changes must be preserved in any production composition.
The useful nonblocking send/deadline/sticky uncertainty/known EOF and frozen-wire
journal changes require composed tests, not original 32/32 evidence alone.

This intake is not a substitute for that production rescue. No new native trial,
formal allocation, implementation correctness, content quorum/current-tree
certificate or sender handoff is inferred. Original Windows/custom-stream,
concurrent EOF and whole-call deadline limits remain. Current source/main
integration, checksum verification and local CI are still pending; source ref
must not be retired yet.
