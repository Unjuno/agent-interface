# A01 source-identity audit archive note

This directory preserves the seven Git-tracked files from branch tip
`0d0f4d4a09e3b6de5b009ac315a3e57e888b195a` of
`research/59-v39-main-source-identity-a01-20261009`. The source files were
copied without regeneration; the archive records one allocation only.

A01's sole frozen audit invocation exited 1 with `HOLD_AUDIT_INPUT` before
producing a source-identity finding. Its audit script incorrectly expected
`ObservableSignalPolicyMonitor` to be defined in the controller module AST.
The retained output records the invocation and failure. A01 was not retried,
and the controller/session were not modified. The separate live threat
exposure remained unrun because the private game lane was unassigned. These
facts scope A01 only; they do not stop unrelated repository work.

The original README refers to `RESULT.md` and `results/source_audit.json`, but
neither file exists at the archived branch tip. They have not been recreated
or inferred. The separate A02 mentioned by the source README is not part of
this A01 archive and has no result here.

The remote source branch remains until PR #9012 integrates this archive. After
that, recheck the exact remote tip and all branch/worktree/PR references before
removing only the redundant branch ref.
