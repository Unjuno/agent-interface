# Idle RPC overlap and held-input cancellation

This preserves evidence for draft [PR #10094](https://github.com/Unjuno/agent-interface/pull/10094)
at `477d54be7cd4e78df1de9601f62617a67558aea5`, based on draft #10074 at
`0675ab810f7ee890d0904b8a402678c81f8dbafb`. It does not add the candidate
to main. Main at the final test freeze was
`21c3333cbe71fb582842fdd29b8b0385853824ce`.

A controlled parent-thread probe showed that the prior candidate could mark
an idle request in flight while an ordinary RPC already owned the RPC lock,
causing cancellation to select the idle branch. Cancellation branches were
mocked; this observation alone does not demonstrate unreleased input. The
proposed fix rejects overlapping admission in either direction. Two targeted
tests passed after the fix, 90 selected WSLc tests passed in both normal and
optimized modes, and a 200-iteration in-process simultaneous-start probe
admitted exactly one operation each time. These do not cover all schedules.

Two private-Xvfb trials used a real spawned owner, with controlled parent-side
pauses before ordinary RPC send or after idle response receipt. The opposing
entry was refused; after resuming, the same owner typed `a`, verified release,
and closed. No input was held during those pauses.

Two further WSLc trials used the existing standard MCP blocked-X-sync test,
including a deliberately delayed X request. An independent X client confirmed
that `a` was held before cancellation. The control made no idle request; the
intervention tried idle and was refused without reserving it. Both independently
observed keys up after release and at the delayed-request horizon; independent
initial and fresh synthetic task-effect oracles passed. In **both** arms the
runtime reported `cancel_unconfirmed` and cleanup `UNKNOWN`. Those observations
do not convert the runtime's uncertain cleanup to confirmed success. Each arm
ran once; this is neither a general recovery guarantee nor a MAP01 result.

`raw.zip` contains frozen source, conditions, reports, retained synthetic-task
artifacts and audit output. `archive-manifest.json` hashes every included entry;
`python audit.py` verifies the archive and re-runs the saved report auditor.
Host-specific `private-command.json`, Python bytecode and the initial Windows
red-test traceback containing a local path are excluded; originals remain
locally. The auditor checks stored evidence consistency, not historical timing
or the absence of unrecorded events. See each included `RESULTS.md` for scope.
