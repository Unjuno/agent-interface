# Reviewed-image reuse: one primary functional pair

**FUNCTIONAL_PAIR_PASS / EFFICIENCY_HOLD.** The primary agent operated both arms in this conversation. No helper model or automated task policy made the GUI decisions.

Before either allocation, the plan fixed seed 991357, B0 then C1 order, 1280x800 private X11 sessions, the same runtime archive, 20 ms text gaps and 100 ms waits. Each arm used a fresh LibreOffice profile. Both had to enter A1=324/A2=145 and save XLSX. The actual three input programs match exactly after excluding instance-specific authority lease ID and expiry. Their source/current revisions and observation assertions also match. The first three image bodies match byte-for-byte across arms. This does not freeze subsequent rendering schedules or remove sequential order/learning effects.

| Observed measure | B0: full images | C1: reviewed references |
|---|---:|---:|
| Saved A1 / A2, independently read from XLSX | 324 / 145 | 324 / 145 |
| MCP calls, including close | 9 | 8 |
| Input programs | 3 | 3 |
| Image-bearing replies retained | 7 | 6 |
| Full images presented | 7 | 4 |
| References presented | 0 | 2 |
| Extra transition observations | 1 | 0 |
| PNG bytes omitted from presentation | 0 | 153,854 |

C1 attempts 4 and 5 refer directly to the explicitly reviewed full image at attempt 3, while current target metadata changes from inspection to committed revision 2. No reference chain is used. The original full MCP images and metadata remain in raw evidence. The reduction attributable to reuse in C1 is two image presentations; the three-image difference between arms also includes B0's extra observation. Reference text has overhead and actual model tokens/cost/cache accounting is unavailable.

B0 attempt 7 showed the format modal and save progress despite metadata identifying the main window. The primary agent did not declare completion or replay input; the planned extra observation at attempt 8 showed saved values with no modal/progress. C1 showed that state at attempt 7. The one-call difference is **not** attributed to image reuse. It demonstrates why input completion and target focus are insufficient evidence of semantic completion. No delay or sensor policy was changed.

Both relays exited 0 and interface close verified empty input state. Fixture process teardown codes are retained in result.json; they are not claims of graceful application exits. Every input program reported completed with verified release and no recovery requirement. Inspection's expected needs_review response has MCP isError=true even when its capture and candidate are valid. The initial post-run verifier incorrectly rejected this flag without examining the body; audit-notes.json preserves that construction failure and the narrowly scoped correction. No GUI allocation was rerun.

## Timing boundaries, not causal performance

| Recorded boundary (seconds) | B0 | C1 |
|---|---:|---:|
| Sum of host send-to-reply intervals | 2.681 | 2.304 |
| Enter-values send to caller's review declaration | 13.100 | 14.739 |
| Confirm-format send to saved-visible declaration | 23.240 | 18.617 |
| First send to saved-visible declaration | 86.116 | 85.590 |

These are host-clock intervals and explicit review declarations, including model/tool/orchestration delays. They do not measure the exact first useful visual feedback instant, model thinking alone, or a causal speedup. Only one pair in fixed order was run, rendering times were not frozen, and provider model/version/per-call usage were unavailable. The same active primary conversation handled both arms without requesting a model change. No human-speed or general efficiency claim follows.

## Reproduction and next integration decision

Run `python3 -O runtime/results/reviewed-image-pair-01/verify.py`. It checks all 131 archived files, pre-allocation source/fixture pins, exact loaded host modules, independently derived request/image counts, acknowledgment/reference identities, actual input-program equality, timing arithmetic, and saved XLSX XML. It does not run the candidate adapter or repeat task input. The public plan/result copies must equal the archived bytes.

Keep the feature opt-in. Exact-image reuse helps repeated-image presentation, but this pair does not establish fewer roundtrips or faster useful feedback. The exposed practical issue remains distinguishing a completed input from a still-changing save screen. Future integration should preserve that distinction and evaluate available research against it; do not substitute focus, elapsed waits, or unchanged pixels for application completion. Actual usage accounting and broader task/domain evidence remain outstanding.
