# Primary presentation failure / partial effect convergence

Base `d66f53dba6e2aea8de36a345968f9f67f18ec7bb`; tested code
`f549aff95f60733089c18e4ffdd16139f652e28d`. The missing test from PR8786
head `5f8fdedaac8fbdaf820ca26dd7ebc7985dc2305a` is adopted without replacing
newer tests. Original complete test and PR snapshot are preserved; the exact
inserted body is joined after explicit line-ending normalization. No production
behavior change. This retains a real supported host failure boundary rather
than inventing a full-body editor or task oracle.

## Current path and discrimination

Seven selected Node host modules pass **126 tests, zero failures/skips**.
They include four new file-effect cells through actual `createPrimaryExchange`
and `createPrimaryCaller`: guarded-local/direct-post, each with presentation
file collision after returned input, or synthetic lost reply after a file effect.
The host callback appends literal A to a local file before returning/throwing.
Its release/image metadata is synthetic, not a physical input certificate.

In all four current cells: one A survives; the first request is retained;
original reply is retained only when actually returned; failed presentation
never overwrites the occupied file; command 1 is consumed; command 2 input is
refused without consuming its ID; explicit public close uses ID2 and its reply
is retained. STOP remains latched after close. For returned input the inner
caller is healthy, proving the outer exchange latch is necessary. A closed
reply here is a fixture response, not native cleanup verification.

A complete copied-module directed control removes only the outer catch's
STOP assignment. All four new tests fail assertions. In the two post-return
cells the input is sent again and disk contains AA; partial-effect cells retain
the inner caller stop but lack the exchange latch. Control source bytes and
exact expression, every cell's witness, copied request/reply/presentation and
effect bytes, full streams, exit codes, PIDs and Node version are retained.
Control `.mjs` files are archived as `.mjs.txt`, preventing test discovery.

The separately implemented saved reader imports no candidate. It checks actual
retained bytes against witness files, literal A, request/reply ownership,
refusal IDs, STOP and explicit close; six contradictory copies are rejected.
It also reads the control's two repeated AA effects. It is an independent
file/custody check, not an application semantic scorer.

## Retained initial collection failure

The first local regression process passed all126 tests. The collector then
raised AttributeError because it assumed TAP while this Node used its default
Unicode reporter. Initial full stdout/stderr, conditions and four witnesses
remain in `initial/`; no PID/structured process receipt survived that collector
failure. The final collector explicitly requests TAP and records both current
and control process receipts. These are repeatable local tests, not a consumed
live allocation; no initial result is presented as a second independent trial.

## Limits and continuation

No GUI, native input, model/provider, WSL/container/resource allocation or
historical science producer ran. The synthetic callback and file effect do not
qualify real platform release, application Save/task success, semantic recovery,
stdio transport delivery/model receipt, power-loss durability or economics.
This is a named supported host failure/custody qualification. Broader #17/#57/
#59 remain open; the role recovery package still needs an actual selected
document/full-body editor adapter and independently scored application effects.
Old PR8786 can close with this continuation only after verified main integration;
its original branch/worktrees remain. All test/script source pins and inert
runners are retained with original local path bindings.
