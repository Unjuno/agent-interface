# V39 retained release trace completeness posthoc A01

## H / T / D / C / U

**H.** The v39 coast-liveness run's existing audit verifies every emitted early `input_released` receipt, but does not report whether every input-bearing interrupted program emitted one. A raw-only reconciliation may show a gap while still proving that the program's terminal receipt verified empty state.

**T.** Freeze the retained allocation files at `6149fc1856ce86de41b168de8ca12690347f524d`; parse `events.jsonl`, `owner-events.json`, `report.json`, the original v2 audit, and the frozen preregistration by Git blob and SHA-256. Pair each cancel request to its terminal, validate terminal and interruption owner release identities/state/times, count prior `keys_held` and early release events, then independently recompute the result and run mutation controls. Do not rerun the game, model, or original allocation.

**D.** `PASS_TRACE_RECONCILIATION_WITH_EARLY_EVENT_GAP` requires all seven cancel requests to match a cancelled terminal with verified empty aggregate release, and every active interruption owner receipt to be verified-empty and ordered from request through terminal. Report event coverage separately. It is a coverage gap, not a failed release.

**C.** Some covers may be cancelled at a step boundary or after no current input remains. Terminal release is the authority for complete closure; absence of an early event alone cannot prove held input or missed release.

**U.** This is a posthoc analysis of one retained live allocation, not a new live exposure. It gives aggregate owner-empty timestamps, not per-key key-up times. The run does not retain independently useful application-feedback timing, and it ended unfinished without MAP01 exit. No runtime repair or causal latency claim follows.

## Result

The retained trace has seven cancel requests and seven matching cancelled terminals, each with verified empty aggregate terminal release. Four cancelled IDs had prior `keys_held` events. Three have a terminal interruption owner-release receipt; all three receipts are verified empty and occur after the cancel request and before terminal. Only one of those three IDs (`plan-3-primary-0-1`) has a matching `input_released` event. Thus early-event coverage is 1/3 for active interrupted programs, while aggregate closure remains verified for all seven cancellations.

For the three interrupted receipts, cancel-request to owner-empty verification spans **0.771–2.652 ms** in this single run. This is not a distribution or a per-key up-time measurement. The one early event was published 12.902 ms after its owner receipt; the two cover interruptions surfaced their verified empty release only in their terminal records. The raw owner receipts contain no per-key release timestamps. The prior audit passes its declared gates; it did not require complete early-event coverage.

The result therefore identifies a telemetry-coverage boundary to examine in a future versioned live run: distinguish per-program early release publication from terminal-only cleanup evidence, and add per-key release measurements if the runtime can retain them without disrupting input-up ordering. This package does not change production code.

## Reproduction

From the repository root, run the v2 analysis and independent audit (the first result and audit are retained unchanged):

```powershell
python -B research/doom/v39_release_trace_completeness_posthoc_a01_20261008/run_audit.py --output RESULT_V2.json
python -B research/doom/v39_release_trace_completeness_posthoc_a01_20261008/audit_result.py --result RESULT_V2.json --output AUDIT_V2.json
python -B -m unittest -v research.doom.v39_release_trace_completeness_posthoc_a01_20261008.test_audit
```

The scripts refuse to overwrite prior results. `RESULT.json` / `AUDIT.json` preserve the first analysis pass; `RESULT_V2.json` / `AUDIT_V2.json` strengthen independent checks of per-ID timing and task outcome. Input provenance and checksums are in `FREEZE.json`; the original allocation and audit remain unchanged. No image, model, game, X11, OS input, container, or GPU was used in this posthoc run.
