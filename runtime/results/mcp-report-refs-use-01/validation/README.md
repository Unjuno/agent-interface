# Post-use integration checks

The native integration runner passed 161 protocol and 68 harness tests (229)
on commit 7623fc37c, including the new backend-attempt and persistence-phase
readback assertions. Full logs and their hashes are in result.json. Docker
container ai-mcp-result-guidance-native-01 completed with exit 0.

The earlier additional readback-only check failed before its body because its
read-only Docker root had no writable temporary directory. The error is retained
in mcp-failure-phase-readback-01-failure.log. Adding a /tmp tmpfs allowed that
one test to run and pass; its output is also retained. Production source was not
changed to address this environment error.

The later main merge adds other contributors' research records; the relevant
CLI/core/integration runner and research/live_control paths have no changes from
the tested base. The archive verifier also passed after that merge. These are
local contract checks, not another live allocation or measured speed benefit.
The parent archive manifest covers the original live/offline archive, not these
later validation files.
