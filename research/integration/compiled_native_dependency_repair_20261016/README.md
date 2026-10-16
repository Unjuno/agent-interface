# Fresh compiled dependencies in native input guards

2026-10-16 JST. Base `f861e2cbf5a4e72281a564ea63c07e1d329296cb`;
tested code `75ac52130e9256b98bb1f13f5159ebbb66ad7b94`.
Decision: **ADOPT_NATIVE_COMPILED_DEPENDENCY_REPAIR**.

## Repair and authority

The [retained counterexample](../compiled_semantic_press_boundary_20261016/README.md)
showed a True graph dependency changing to False/unknown in the native pre-input
capture while current execution still sent Submit. Compiled admission now freezes
the symbol identity/dependency names in its one-use authorization. Execution
registers a frozen native input guard; its trusted read-only perception callback
checks those predicates on the native check's fresh RGB, requiring exact True.
Missing guard capability is rejected at adapter construction before capture.

`NativeHandleBridge.input_guard(..., interaction='keyboard')` keeps keyboard as
the compatible default with a nonempty tail. Explicit click/move guards permit
empty tails. The guard freezes interaction, offset and tail; a different program
is refused. Native alias/focus/scope/generation, source freshness, original
deadline and post-callback association checks still run. Perception failure or
unknown/False identity/dependency stops later task input. Releases bypass the
callback, including when a modifier is already held. The callback adds no retry,
remint, lease renewal or task scoring.

These are input dependencies, not all graph branch conditions or post-action
effects: entry does not require its eventual value effect to already be True.
The ordinary bridge API changes only when a caller explicitly registers a guard;
compiled execution now always registers one. The memory-only Bridge test fixture
implements the new callback contract on its current synthetic image; it does not
pretend to implement the actual native fresh-capture machinery.

## Executed checks

Nine new actual-bridge methods retain 18 rows per mode:

| Conditions | Interaction / expected result |
|---|---|
| Stable dependencies | keyboard, click, move complete with verified fake readback |
| False, unknown, missing identity, callback exception | Each of keyboard/click/move refuses before any fake input |
| Dependency changes while CTRL held | No `a` press; CTRL release and verified fake neutral readback |
| Dependency changes after pointer motion | No button press; cleanup verified |
| Original authorization expired | No callback recheck or input |

The ninth method also checks missing guard capability before capture (no row).
Two additional API methods verify frozen interaction mismatch, unsupported
interaction and the existing empty-default-keyboard rejection. The full affected
selection passes **55 modules / 385 unique methods**, zero failures/errors/skips,
in normal and actual optimized Python. This includes the prior caller/core/native
composition selection; it is not all platform/native suites. Registry includes
the new regression once in harness. DISPLAY is absent in child environments.

The complete original compiled module from the base, loaded canonically with
the same repaired bridge/fixture/test sources, fails **18 assertions in nine
methods**, zero errors, in each mode. This isolates the missing compiled guard
connection; it is not a reconstruction of the entire historical environment.
The initial eight-method RED retains 17 assertion failures; the added ninth
missing-capability method is covered by the final pinned controls.

A separate actual caller/graph/bridge probe compares the pinned original module
with the repair under identical current bridge/fixture conditions. Each arm has
four cells per mode. Stable executes two chords/prefix2 in both; generation
change stops after one in both. Original False/unknown still execute two chords;
repair refuses the second, preserving prefix1. The caller never asserts task
success: stable remains TASK_NOT_VERIFIED with unavailable outer effect, and
refusal remains EXECUTION_INCOMPLETE. The control does not nest an additional
manual guard around the repaired compiled guard.

## Evidence and limits

Eight deterministic gzip archives retain full selected ROWS/RECORDS, all 18 direct
rows, four caller cells in each original/repaired arm, exact bridge files as hex,
native captures, callbacks, releases and countercontrol streams. Conditions,
process IDs, actual optimization flags and commands are retained. SOURCE_PINS
records 92 selected Git/worktree source/data joins, not a full import closure.
CONTROL_SOURCE_PINS identifies the original module. CONDITIONS' base denotes
the tested repair code; inherited old_prs is historical navigation only.

The saved-only reader joins terminals to native execution, checks frozen needed
predicates, reopens actual retained PNG bytes and their SHA to verify the marker,
and verifies direct plus caller outcomes. It rejects six copied contradictions
in each mode. It imports no candidate and performs no independent app scoring.
Runner/probe `.py.txt` files are inert references with original local bindings.

All platform setup, capture/XTest transport, keymap/process evidence and semantic
markers are Fake X fixtures. No real display/input, model/provider, WSL/container
or formal allocation was used. Trusted perception code remains synchronous
unless the caller selects the existing observation worker; this repair does not
bound a blocked callback or native I/O. Sampled checks do not eliminate changes
between capture and press, competing writers, or real perception error. The
known pre-input capture gap is narrowed; independent application effect, native
release timing, finite semantic recovery, live model/MCP and matched economics
remain unqualified. Keep #17/#59/#57 open.
