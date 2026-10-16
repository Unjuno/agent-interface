# Reserve post-controller scoring with the final program

Experimental interactive_v19 adds optional `finish_after: true` on submit. A
valid submission reserves the episode's final program. Further submits are rejected;
clock/cancel and applicable pointer replies remain available. After its terminal,
a separate finalizer closes executor admission and runs the independent task oracle.
The result names final_program. A later finish command only joins and cleans up,
without rescoring. Invalid submissions clear the reservation and can be corrected.

This is benchmark lifecycle scheduling, not a speculative input branch or a semantic
detector in the controller. All scoring runs post-controller; no scored result can
drive another program in the same episode. A failure result also closes the episode.
Terminal status and independent task outcome remain distinct. The ordinary scorer
may poll saved output up to its existing timeout; this does not expand input authority.

Actual assistant final-score-calc-01 repeats journal-calc-02's seed, goal and accepted
steps: enter 532/590, save, view format modal, confirm Excel with final scoring
reserved. Both saved workbooks pass; forty exact frames/source manifests and all
declared image references pass comparison. The added post-score settle submission
is a negative test and is rejected. Exactly one evaluation is emitted, before the
cleanup finish command. The final receipt image was also viewed by the assistant.

| Endpoint | Explicit finish baseline | Reserved final score |
|---|---:|---:|
| Final terminal → independent score known | 30,650.157 ms | 17.317 ms |
| First capture → score known | 97.515 s | 50.430 s |
| Modal terminal → confirm command | 39.442 s | 23.816 s |

Only removal of the extra scoring-request boundary is mechanically demonstrated.
These are sequential familiar-task runs, with variable planner/tool delays. Total
time improvement cannot all be attributed to the feature. Score-known is a runtime
endpoint, not model receipt, user recognition or cleanup completion. Cleanup and a
post-score negative test still require commands. Exact model settings/tokens remain
unrecorded; no human-cadence claim follows. JSON totals include post-score diagnostics
and should not be read as token comparisons.

Negative subprocess cohort final-score-cancel-01 incorrectly waited for step_started,
which compact presentation suppresses; it never sent cancel. The program completed,
independent scoring failed, and the probe timed out. Its child was killed; the three
remaining private fixture processes were identified by their shared Xauthority path
and terminated. This failure is retained. V2 waits for delivered acceptance, sends
cancel, and verifies cancelled/released plus failed scoring. It also checks an invalid
final reservation can be followed by a valid one. Both negative cohorts' frames and
source hashes were checked. The test uses a 100 ms delay, not proof of exact key-down
timing. Probe timeout cleanup remains a research limitation.

Finalization is signaled in emit's finally so output exceptions cannot silently omit
the terminal signal. Permanent blocked output can still block progress; finalizer I/O
errors and failed evaluation delivery need an explicit error contract before promotion.
The default entrypoint is unchanged. Next separate production semantic verification
from privileged benchmark scoring and test finalization failures without weakening
the post-controller oracle boundary.
