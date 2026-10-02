# Real Calc compiled pixel admission: invalid native alias

Disposition: FAIL_SETUP_INVALID_NATIVE_ALIAS / HOLD_COMPILED_CALC_WORKFLOW.
One allocation seed1002082. Plan/scaffold frozen89e90e9bd, packaged runtime
source936a86c1026e70ee68221c773b5e367b4ed1947a before launch. WSL package3.0.1,
Ubuntu WSL2, private1280x800 Xvfb/Openbox/LibreOffice24.2.
This was the concrete #57 gate connecting previously scoped pixel reading to
the existing compiled.run API, not another caller framework or new benchmark.

## Actual primary use and retained failure

The primary viewed the original blank sheet PNG, grounded the B header context
at162,172 and two cell regions, then explicitly requested mint sheet-context.
The actual registry rejected that hyphenated alias: names must match
[a-z][a-z0-9_]{0,31}. This is a primary-authored scaffold contract mistake, not
a failure of OCR, conditional continuation or Calc saving. Those stages never ran.
One observe completed, one mint failed, zero input dispatches/graph invocations.
The owner94780 exited1; all three owned children were terminal (Calc255,
Openbox0,Xvfb0). Independent post-terminal workbook scoring found empty cells and
taskfalse. No retry/reset/graph rerun, no alias correction in this frozen case.

The four pre-launch method tests passed against a mock resolver that omitted
actual native alias validation. They therefore did not qualify the live contract.
Initial construction also failed on an unmaterialized sparse keeper path; first
two test fixture versions lacked bridge output/artifact metadata. All failures
are retained. Corrections to those mocks did not make the invalid live alias valid.

## Product correction

Commit c19ed3825 adds alias preflight to the existing X11 compiled adapter, using
the handle store's existing ALIAS expression rather than a second rule.
Invalid target_reference names now fail before native capture/perception/effect
callbacks. Graph symbol labels remain separate and can still contain hyphens.
This does not mint references, grant authority, renew scope, replay input, expose
a new MCP route or qualify a complete Calc workflow. The frozen failed helper
remains unchanged; a future successor must use valid references such as sheet_context
and validate the real native contract before any new allocation.

RED four invalid-alias subcases fail before the production fix. Targeted adapter
and core tests51 pass normal and optimized Python afterward. Local native CI:
protocol383 and harness185 pass. The corrected-package archive is pinned to
c19ed3825; isolated import/probe rejects the same invalid interface without a
bridge/display/capture/callback/input. The original failed runtime.pyz is preserved.
No matched speed/token benefit or successful compiled Calc execution follows.

## Accounting and image provenance

The actual source window21:37:19.600Z through21:42:21.989Z covers authoring,
failed constructions, launch, model grounding and terminal/oracle observation:
14 unique model responses; input1667482 (cached1647872 subset, uncached19610),
output9805 (reasoning2063 subset), total1677287; cache-write0, price/cost null.
These are growing whole-context response charges, not per-image/callback/arm costs.
Earlier issue/source discovery and later diagnosis/product fix/tests/publication
are outside the window and unmeasured, not zero. No comparison with old cases.
Exact source lines/hashes/call boundaries and one original model-delivered PNG
are independently replayed under normal and optimized Python. This verifies
encoded image identity, not provider preprocessing or model comprehension.
The302.389s source-window span includes authoring and is not a GUI task speed.
No semantic completion timestamp exists for this failed task.

Failure-record audit reconstructs the original command, zero dispatch/graph,
image/grounding identity, terminal children and empty saved score.
Private profiles/cache/lock files remain local. Full six-phase A/B/C comparison,
equivalent online assistance, saved-effect/target-handoff/public delivery and
economic decision remain incomplete. This record finalizes this failed block.
