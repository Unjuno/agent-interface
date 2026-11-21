# R02 result

Status: `PASS_SCOPED_SYNTHETIC_COMPOSITION`.

The frozen positive and missing-usage control each ran once. In the positive
case, the public caller observed one late-usage receipt after an independently
recorded UNKNOWN score; the composed standard measured run retained complete
usage at 18 input and 3 output tokens. The control retained no usage row and
projected incomplete usage with null totals. Both task scores remain UNKNOWN,
there are no `tool_call` events, effect time is null, and Relay calls are zero.
All recorder raw references are retained and hash-bound.

Validation before the one-shot experiment: the two synthetic contract tests
passed 2/2 normally and 2/2 with `-O` (logs and exit codes are retained).
The experiment itself passed with exit code 0. It was not repeated.

The first post-run audit attempt failed because it compared a Git blob ID with
the CRLF-converted Windows worktree bytes. The source bytes were unchanged:
`git hash-object --path=<file>` produced the pinned blob IDs. The auditor was
updated to compare Git-clean-normalized object IDs, and that audit passed.
The preserved failed audit log is part of the record. A final audit further
checks task-score/effect/tool-event boundaries and the complete SHA256SUMS
manifest. Clean-main audits exposed Windows checkout conversion of packet
text files and ignored Python bytecode. The packet now disables line-ending
conversion for all files; the auditor excludes bytecode and checks this
attribute rule directly. `.gitattributes` itself remains outside SHA256SUMS
because checkout can change its line endings without changing its rule.

This demonstrates only a synthetic accounting composition on frozen source
revision `d08596ee0590ba6a9531075a5769c0ac4abc1ec1`. It does not establish a
live provider call, provider billing, task success, input release, GUI effect,
matched A/B/C economics, or recovery reliability. It does not close Issue #57.
