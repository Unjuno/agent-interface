# Opt-in public dispatch summaries

`detail="summary", compact=true, report_refs=true` summarizes known successful
public dispatches, including short nonpaced save programs. The default full
receipt and existing paced brief projection are unchanged. The new schema is
explicitly partial; follow `presentation.retrieve` for the complete retained
report without replaying input. All capture/release/activation records, images,
outcome fields and call identity stay present. Failed, incomplete, inconsistent
or unfamiliar omitted shapes remain full. No execution policy changes.

## Primary use and same-report comparison

A fresh private Ubuntu WSL/Xvfb/Tk session used the built public runtime through
the stdio relay. The primary entered `http://v_w` with an explicit post-click
50 ms delay, reviewed the unsaved value image, saved in a separate nonpaced
program, reviewed the saved image, retrieved the full save report, exercised a
planned unsupported-verify refusal, and closed. The independent post-close file
is exactly `http://v_w`. The refused program emitted zero input and stayed full.
Six MCP calls, two executed input programs, one refused program, one full lookup,
three images and three primary review records. No repair was needed.

| Same report | Full JSON bytes | Prior brief bytes | New summary bytes |
| --- | ---: | ---: | ---: |
| Paced input | 9,080 | 5,757 | 3,799 |
| Nonpaced save | 4,652 | 4,652 | 3,716 |
| Total | 13,732 | 10,409 | 7,515 |

These are canonical UTF-8 JSON bytes for identical retained reports: 45.27% below
full and 27.80% below the prior brief option. Images are separate and unchanged.
Actual provider tokens/cost and matched latency are unmeasured. Full retrieval
adds a call and response; it is not included in this per-report compression
comparison or claimed to reduce total interaction cost. The older four-report
intake is retained separately and is not pooled with this fresh use.

## Discovered limitation and correction

Primary build source was `82ecded8b0eab920a61d8005be3215fe4974f3e2`.
Inspection of its real full lookup showed that retained results have no live
owner snapshot at top level. The initial summary gate consequently left such
lookups full. Two newly added tests reproduced this limitation; their failure
log is preserved. Commit `f00adc848` keeps historical session evidence in
`receipt.reported_session` when there is no live wrapper snapshot. It grants no
current binding or authority. The final archived build contains this correction.
Both actual primary dispatch summaries are byte-identical under the corrected
implementation; live input was not repeated for a presentation-only fix.

The corrected real presentation/retrieval path was checked with dispatch stubbed
to the retained report (no GUI input; presentation was not stubbed). Initial
setup incorrectly referenced the old image outside the new call directory and
was correctly refused as `image outside run directory`; it failed with a missing
summary marker. A fresh setup copied the exact PNG inside the new call directory
and adjusted only its path. It preserved historical session data, retrieved an
identical full report and invoked the dispatch stub only once. Both setups stay
in the archive, clearly separate from live primary evidence.

## Validation and reproduction

Focused tests pass (8 methods including existing paced-brief tests), with 20
failure/extension/inconsistency controls. Final native suites pass: 290 protocol
and 128 harness tests, including portable distribution checks. Default full,
partial decoder rejection, preserved literal metadata, historical/live session
distinctions and input-free full retrieval are covered. The final build succeeds.

All 83 files are retained in `raw.tar.gz`: primary requests/replies/images,
reviews/effects/cleanup, both builds, before/after tests, real-presentation STOP
and PASS, and the initial intake. `host-timing.json` names unmeasured metrics.
Transport exit is 0; owned processes are terminal, with actual teardown statuses
retained (not rewritten as all-zero). Xlib startup diagnostics remain in scope.

Run `python3 -O runtime/results/public-summary-01/verify.py`. It verifies archive
bytes and uses the archived final implementation to reconstruct both primary
summaries, checks full lookup equality, the zero-input refusal and final effect,
and recomputes the byte comparison. It does not dispatch, capture or rerun GUI
allocations. The archived build is used so future source edits cannot silently
change this historical result.
