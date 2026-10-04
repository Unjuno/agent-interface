# MCP shutdown rescue in progress

Source `d632462d3cf8f0ecf5d7d4e8aadc4ae64bcbe3b1`, original draft PR6947.
Runtime server and session tests restored from its exact committed images;
108 original archive files remain unchanged, including Windows shared-entry
FAIL and all intermediate source snapshots. This successor is not approval
of the original draft or a native input/release proof.

Fresh local Python3.12 / MCP1.30.0 results:

- Current-server seven added regressions: exit1, six failures and one error.
  Entered operations/persistence can lose shutdown custody; pending cancelled
  submission leaves busy; cancelled shutdown waiter cancels the worker handle.
  Persistence RED also contains a secondary close assertion during cleanup.
- Restored candidate four-module suite: 106 methods, one failure and one error.
  All seven added regression methods individually report `ok`.
  Remaining failure: PublicCompiledOwnerTests.test_final_image_uses_new_call_root_without_extra_observation.
  Remaining error: PublicMCPTests.test_portable_stdio_runs_outside_checkout,
  nested assertion that call_directory is beneath root/calls.
  Both concern lexical path containment; cause is not yet independently proved.
- Original data-only verify.py: exit0; consistency only, not authentication.

Raw new transcripts remain in workspace outputs `mcp6947-rescue-red.log`,
`mcp6947-rescue-green.log`, `mcp6947-archive-verify.log`; they must be preserved
in a reviewable successor before final delivery. No full local CI PASS or
main integration is claimed. Do not skip or weaken the two remaining tests.
Compare against unchanged baseline and investigate actual path normalization.
Keep original branch until adopted, source tagged, and dependencies checked.

## Subsequent diagnosis and qualified GREEN

The two remaining path assertions also fail with the unchanged server
(baseline-path-fail.log). macOS default `/var/folders/.../T` resolves to
`/private/var/folders/.../T`; the application resolves saved paths while these
tests compare against the unresolved temporary root. No production or test
change was made to suppress the assertions. With canonical `TMPDIR=/private/tmp`,
all106 pass normally. With the **same original temporary directory** specified
using its canonical `/private/var/folders/.../T` spelling, all106 pass under `-O`.
Both settings and first failures are recorded in separate raw logs here.
This establishes a path-spelling fixture limitation, not a GUI/native-input result.
Shared native integration remains a separate gate; no blanket suite claim follows.
