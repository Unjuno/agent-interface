# Exact-value form admission through the guarded X11 adapter

2026-10-16 JST. Base `04e2602e2cc0d916809ae4a7cf65877e31918e77`;
tested code `f8539b347b83601b5ee721d6c40510f4069929f5`.
Decision: **ADOPT_GUARDED_FORM_ADMISSION_REPAIR**. Ordinary local repair;
no native display/input, provider/model, WSL/container or allocation was run.

## Actual incompatible contracts

The exact-value form's entry branch requires `field_value_matches_task=False`,
then enters the value and expects that predicate to become True. But its field
symbol declared the same predicate as an identity dependency. The actual
`runtime.guarded_x11_v1.compiled._Adapter.admit` requires all symbol dependencies
to be True. Therefore an empty field selected by the graph could never reach
reference resolution or input: the composition yielded `missing_symbol`.
Caller-only fixtures with unconditional admission did not exercise this mismatch.

The repair removes only that post-entry value predicate from the **field's**
identity dependencies. Field presence and reference resolution still gate entry;
the entry branch still requires a not-yet-matching value. The post-entry effect,
Submit branch and **Submit symbol** still require the exact value. No authority,
automatic retry, replay or semantic compensation is added. Frozen historical
source copies and outcomes are unchanged.

## What ran

Seven new methods execute the actual form compiler and guarded adapter, including
its graph, capture/predicate association, dependency checks, reference resolution,
one-use authorization, execute normalization, effect checks and saved receipt.
The existing `test_compiled.Bridge` is an explicitly **memory-only bridge fixture**:
its RGB phase, reference store, focus, input and release reports are synthetic.
This does not qualify NativeHandleBridge, X transport, native ownership, physical
release or application effects. The serialized raw rows contain receipts,
admissions and fake input-call records; no native frames were acquired.

| Case | Actual guarded-adapter result with fixture values |
|---|---|
| Missing value, then exact value observed | Two input callbacks (`field`, `submit`), two verified fixture releases, method complete |
| Wrong value after entry | One completed entry; `effect_failed`; no Submit |
| Unknown value after entry | One completed entry; `effect_unavailable`; no Submit |
| Field missing | No reference resolution/input |
| Submit missing after exact entry | One completed entry; no Submit |
| Already exact initially | No input; this empty-entry recipe does not automatically submit |
| Direct Submit admission while value is False | Refused before resolution, no authorization/input |

The first six-method RED failed four assertions, zero errors. Final seven-method
tests pass normal and actual optimized Python. Complete pinned original compiler
source still fails four assertions in that final module in both modes. A directed
complete-module control removing the **Submit** value dependency fails the direct
admission method, proving that removing both value gates is not an acceptable fix.
That synthetic control issues a fixture authorization, not real input authority.

Final affected selection: **53 modules / 366 methods**, zero failures/errors/skips
in both modes. It includes the prior 223-method caller/model/core selection,
136 guarded X11 methods and these seven new methods. This is not all native or
platform suites. `DISPLAY` was removed from the child environment; dependencies
including Pillow and python-xlib versions are recorded in CONDITIONS.

## Evidence and readback

[SOURCE_PINS.json](SOURCE_PINS.json) records 86 selected source/data joins with
separate Git/worktree byte digests. It is not a claim of a complete dependency
closure. CONDITIONS' base denotes the tested repair code. Original compiler and
the exact counterfactual expression/hash are in [CONTROL_SOURCE_PINS.json](CONTROL_SOURCE_PINS.json).
Complete stdout/stderr and process receipts are retained; six full record
archives have uncompressed byte checks in [RECORD_ARCHIVES.json](RECORD_ARCHIVES.json).
The earlier RED/green streams are construction history; final controls use the
committed test source rather than reconstructing an earlier test version.

A separate saved-only reader checks all seven new rows, prefix/input aliases,
fixture release flags, reference/effect counts and both counterexamples. It
rejects six copied contradictions per reader mode: hidden input, lost prefix,
wrong-value completion, false Submit admission, wrong reference and inconsistent
release. It does not import the candidate or independently score an application.
The three `.py.txt` runner/readers and original compiler copy are inert reference
data with original local path bindings, not registered actors. The new regression
is registered once in the existing harness suite.

## Remaining integration

This closes an actual form/guarded-adapter compatibility failure. The separate
[v3 caller connection](../../live_control/COMPILED_CALLER_V3.md) still requires a
domain builder that maps the final target/check to real scope/aliases, and actual
per-action authority/effect qualification. This packet does not certify that full
caller-to-NativeHandleBridge path, live task success, bounded semantic recovery,
physical release time, provider accounting or matched/second-domain economics.
Reuse the repaired entry/dependency distinction in that next composition rather
than bypassing the guarded admission checks. #17/#59/#57 remain open.
