# Finalization is a closure decision, not an ordinary effect query

The existing caller's --boundary outcome requests finish_after=true. Runtime v28
reserves the final program, closes admission after it terminates, and performs
independent evaluation. This is not a non-final check that permits recovery after
a negative evaluation. --boundary terminal retains the possibility of another
explicit input program but does not independently establish task success.

probe_confirmation_boundary.py compares these paths in two scripted private
Linux/X11 browser runs, using the same seed, initial draft, replacement steps,
confirmation steps and v28/v12/v6 stack. Only the first submission's requested
boundary differs; both subsequently attempt the confirmation program. The fixture
is known and the controller does not infer its behavior from images.

| First submission boundary | First HTTP attempt | Later confirmation | Final score | Exact frames |
|---|---|---|---|---:|
| outcome: finalize now | not saved | rejected: final program already reserved | false | 16 |
| terminal: review first | not saved | admitted; confirmed value saved | true | 22 |

The negative case is an expected architectural counterexample, not a passing
task. Both first submission programs complete and release input successfully;
neither alone achieves the application effect. The successful route deliberately
defers closure. There is exactly one independent evaluation per run, with matching
admitted request lineage. The delivered record prefixes and every frame round-trip
exactly. Runtime source hashes match. No timeouts are converted to success.

The v2 fixture's attempt log survives cleanup in both complete GUI runs. It retains
[false] for the premature-final case and [false, true] for the recovery case. A
checkpoint artifact saves the first attempt and caller task-success field: false
for the closed/evaluated route, absent/null for terminal-only review. This is a
harness-side log snapshot, not a new planner-visible runtime verifier. It cannot
retroactively recover the lost v1 self-use log.

## Decision and remaining gap

Document and preserve terminal review for operations with known additional visual
decisions. Do not label --boundary outcome as a harmless wait-for-evidence option.
No default or public runtime protocol changes in this experiment.

An admission-preserving effect checkpoint remains a candidate requiring a separate
contract. It must distinguish a currently absent artifact from a closed-window
contradiction, allow unavailable evidence, bind the sampled target and time, and
avoid blocking input cancellation while a verifier runs. A later matching artifact
does not establish that the earlier action caused it. A fixture-only server log
would not fulfill a universal GUI verifier. These requirements follow the existing
[Issue #34](https://github.com/Unjuno/agent-interface/issues/34); this study does not
complete its required/forbidden/preserved-effect experiments on Calc and Inkscape.

The two runs are fixed-order scripted functional comparisons. There is no measured
model reasoning, unfamiliar application completion policy, timing speedup, actual
token cost, or cross-domain generalization. More image suppression or a longer
lease would not solve the premature closure shown here.

Evidence: results/confirmation-boundary-01 with per-call requests, replies,
checkpoints, server logs, saved result, frames and source manifests. The correction
to log storage now has full GUI evidence in addition to the earlier HTTP-only test.
