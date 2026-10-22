# Converge #7954: callback failures with compiled receipts

2026-10-16 JST. Base `b0ffed8920706265adc0d44987556aaf41c78ee2`;
tested code `db8f64706b7342e981612506f055c82d3ccc02db`.
Decision: **ADOPT_CURRENT_CALLBACK_RECEIPT_REPAIR_CONVERGE_PR7954**.

## Previously missing repair

[#7954](https://github.com/Unjuno/agent-interface/pull/7954) remained open at
`f18c378f1eef3f48ea10207e17eb7f184bb5d8a5`, outside main ancestry. Current
core still let verifier/journal exceptions escape after completed input and
verified release. The newer v3 helper could therefore receive no core receipt;
its separate publication-sink repair did not fix this boundary.

The PR's [self-check](https://github.com/Unjuno/agent-interface/pull/7954#issuecomment-6034510392)
also found terminal journal failure hidden when the verifier had already caused
RUNTIME_FAILED. This convergence repairs that omission rather than importing
the old implementation wholesale.

All six original source files are preserved as exact inert `.txt` bytes with
Git blob/SHA pins in [PR7954_ORIGINAL_FILES.json](PR7954_ORIGINAL_FILES.json).
[PR7954_SNAPSHOT.json](PR7954_SNAPSHOT.json) retains pre-closure body/comments/
file list; it is a dated snapshot, not later live PR state.

| Original contribution | Current disposition |
|---|---|
| Core repair | Adapted while preserving newer unresolved-input, association, strict return validation and defensive-copy safeguards |
| Two original test files | Three methods adopted with only package-import AST change |
| Guarded verifier witness | Retained before core consumes the ordinary exception |
| Original guarded regression | Covered by new memory Bridge and actual bridge/caller tests |
| Compiled documentation | Current guide updated; original bytes retained |
| Terminal-journal self-check | Covered by core plus guarded caller tests and an omission control |

## Current contract

Ordinary verifier exceptions return RUNTIME_FAILED/effect_unavailable with the
completed prefix, verified release, pending effect and effect_verification_failed
event. The guarded adapter attempts to save the scoped original exception
witness first. No subsequent input or outer task verifier runs.

Once execute was attempted, ordinary journal failure is sticky: return
RUNTIME_FAILED/execution_failed, retain private critical evidence and prefix,
skip future journal writes and stop further task input. Terminal sink failure
always records journal_write_failed, even if another error already produced
RUNTIME_FAILED. Both error types survive, and the returned terminal event agrees
with the receipt. The sink may have seen a tentative terminal verdict before
raising; that attempt does not establish successful durable publication.

Pre-dispatch journal exceptions preserve their existing propagation contract,
as required by current tests. Fatal BaseException stops and malformed-return
validation also retain their existing behavior. This intentionally adapts the
old proposal. It does not make every post-input failure return a receipt.
Other adapter exceptions, failed raw/final receipt publication, blocked callbacks
and crash durability remain outside scope. The separate v3 sink-failure custody
still applies when core has returned a receipt.

## Executed evidence

Fourteen focused methods comprise the original three, seven core cases and four
guarded/caller cases. New raw rows number six core plus four memory/native caller
rows per mode. They cover compound failure, mutation, no sink retry, prefix/
release retention and one chord only before failure. Fatal propagation checks
the same original exception object. The composed cases use actual form, graph,
guarded adapter, NativeHandleBridge/store/session and v3 helper with Fake X
transport, or the explicit memory Bridge fixture for saved receipt/witness.

The affected selection passes **64 modules / 463 unique methods**, zero
failures/errors/skips, in normal and actual optimized Python. Substituting the
complete original current-main core into the same fourteen focused methods
produces **eight assertion failures and three errors** per mode. Those errors
are the expected escaped RuntimeError/OSError callbacks, not import/collection
or environment errors. A directed complete-module control reintroducing the
terminal-failure omission produces **two failures, zero errors** per mode.
The initial ten-method RED retains five failures/two callback errors; final
controls use all committed fourteen methods.

106 selected current source/data joins, six full gzip record archives, control
expressions/hashes, process IDs/optimization, complete streams and RED are
preserved. These pins are not an import closure or every platform suite.
CONDITIONS' base is tested code; inherited old_prs is historical navigation.
Saved-only readback checks prefix/release/pending/dual-cause/witness and caller
joins, rejecting six copied contradictions in each mode. It imports no candidate
and scores no application. `.py.txt` tools are inert with original local path
bindings. No historical experiment producer was rerun.

No display, native input, model/provider, WSL/container or allocation ran. Inert
callbacks and Fake X do not establish real task success, physical release
bounds, durable logging, finite semantic recovery or matched economics. Keep
#57/#59/#17 open. The old PR can converge here with its ideas and original bytes
preserved; no old branch or unrelated worktree needs deletion. Remaining adapter/
publication failures and independently scored task effects are the next gates.

Publication-only adaptation: the two adopted tests have excess EOF blank lines
removed after tested code `db8f64706b7342e981612506f055c82d3ccc02db`.
`PUBLICATION_SOURCE_JOINS.json` records exact byte hashes and equal Python ASTs.
Original tested pins and runs remain unchanged; no behavioral rerun is claimed.
