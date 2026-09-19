# Combined native batch use

One fresh private WSL X11 allocation, primary assistant, seed991111 (Calc) and
991112 (Inkscape), max6 stages, 2ms text gaps. The pre-run PLAN is retained.
No sensor, helper model, Docker restart, or replay was used.

Three requests completed both public tasks:
1. Click the observed rectangle edge, wait50ms, Right repeat18, wait50ms,
   save, wait100ms, Alt+Tab. The returned frame showed Calc with A1 selected.
2. Keyboard-only enter190, Return, enter676, Return, wait100ms, save.
   The returned frame showed both values and the format confirmation dialog.
3. Click the observed Use Excel button, wait100ms, finish_after=true.
   The returned frame showed the worksheet without the dialog.

Saved-file inspection independently confirms Calc A1=190/A2=676/B1 absent and
Inkscape x86/y50/width40/height30/no transform. Both original task scores pass.
Inkscape's public goal is x>50.5 with geometry preserved, not exactly x86.
All three inputs completed with verified releases; program emissions47/20/3.
All three feedback results remain needs_review across focus/dialog transitions.
The final summary correctly displays evaluation_success=true alongside this
feedback status. This presentation does not repair or infer feedback readiness.

Tracked cleanup completed and owner exec37215 returned0. Tracked process codes
include1,255,-15: this does not prove normal application shutdown or all
descendant termination. The final image precedes scoring/cleanup, not a live
post-cleanup screen. No general paint-coherence result is inferred from it.

`client-exchanges.json` retains caller exchange timestamps. They exclude model
thinking and host tool transport. There is no matched baseline for this combined
task, so no latency, token reduction or human-tempo performance claim is made.
The current primary assistant used the summary on each response; there is no
counterbalanced model-accuracy comparison.

`timing.py` accounts for the32.423476383s from first client entry to final return:
2.130018658s inside exchanges and30.293457725s between them (93.43%). Outer
gaps are15.241700170s and15.051757555s. They combine host transport, presentation,
deliberation and request assembly and cannot be attributed to one component.
Setup is excluded. Prioritize direct caller integration and matched measurements;
this accounting neither estimates first-useful-feedback latency nor proves that
all outer time is removable. An initial shell one-liner failed quotation parsing
before executing Python; the retained standalone script avoids that host quoting
fragility and reads only the existing records.

Run `python3 runtime/results/native-combined-batch-01/audit.py` from any checkout.
It validates81 frozen evidence files,37 image links, request/source/reply binding,
release records and saved files without importing the candidate controller.
Original absolute image paths are retained; the auditor maps their filenames
to archived images. Source snapshots were captured after the run with no source
edits during it; provenance identifies the exact running commit. Additional
README/auditor/client-exchange files are tracked by Git, outside manifest scope.

Integration triage: #2985/#2995 reports scoped semantic FIFO ordering, but the
merged PR provides only REPORT.md and RESULT.json, not the candidate or raw
transition corpus. Do not integrate an uninspectable queue implementation from
that claim. #2293 still requires real shared-resource/concurrent GUI evidence;
the serial Alt+Tab run here does not satisfy that parallelism gate. #3199 concerns
subagent orchestration and is outside this primary-assistant integration run.
