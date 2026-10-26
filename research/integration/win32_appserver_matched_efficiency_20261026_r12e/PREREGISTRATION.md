# R12e preregistration — transition-scoped compiled effect checks

R12–R12d remain preserved. In R12d, direct pair 1 passed the complete task and cleanup gates. The compiled arm dispatched click+type once and received a retained release-confirmed terminal result, then yielded before save because the caller verifier incorrectly required the final saved effect for the intermediate click-and-type action. The fixture was unsaved at close; owner and foreground cleanup passed. This packet uses four new fixtures and oracle IDs. The caller verifier now checks each transition's own expected predicate and independently checks final saved file/oracle.

# R12d preregistration — bounded response wait

R12, R12b and R12c remain preserved. R12c fixed caller observation sequences and retained public refusal responses; those responses show INVALID_RESPONSE_WAIT because 15,000 ms exceeded the standard server's 10,000 ms bound. This packet uses four new fixtures and oracle IDs and sets the wait to 10,000 ms. It preserves the exact public calls, outputs, and cleanup outcomes.

# R12c preregistration — explicit caller sequence study

R12 and R12b are retained at their original packet paths with raw results and failures intact. R12b reached one initial AppServer turn per cell but supplied no caller observation sequence to direct dispatch; the four fixture event streams contain only ready and no input action, and cleanup restored the original foreground. This packet uses four new fixtures and oracle IDs, assigns monotonically increasing caller sequences to standard observations, and persists complete public dispatch responses before extracting receipts so refusals remain diagnosable.

# R12b preregistration — corrected live Win32 matched study

R12's first run is retained at esearch/integration/win32_appserver_matched_efficiency_20261026_r12/. It launched and cleanly exited four blank owned fixtures but failed while constructing the supervised server, before AppServer initialization, model calls, or input dispatch, because the runner omitted the paired native producer factory. This new preregistered attempt fixes that harness configuration. It uses four new fixtures and fresh oracle IDs; it does not overwrite or reclassify R12.

# R12 preregistration — live Win32 direct versus compiled efficiency

R12 is a fixed four-cell, counterbalanced, repeated task study on the authorized Windows PC. It does not change or replay R05–R11. Conditions and runner hashes must be frozen before the first fixture starts. Each cell gets a new fixture process, MCP session, AppServer planner session and independent oracle ID. Stop the series if a cell leaves unresolved input, an owned process, or foreground state; never replay an ambiguous action.

## Task and arms

Each cell begins from the same blank 400×180 owned fixture. The model selects a bounded click point from the public observation. Stage one clicks and types only `office`, making the application text visible while leaving it unsaved. Stage two saves and releases all inputs. The independent exact effect is `{saved:true,text:"office",clicked:true}`.

The direct arm asks the model again after a fresh post-stage-one screenshot whether the visible fixture state warrants saving. It then submits one standard public save action. The compiled arm runs a validated two-transition `run_public_compiled` graph: it observes the text/click state locally, then saves without a second model turn. Both arms use the same model, effort, initial prompt, coordinate bounds, fixture, action semantics, standard supervised Win32 backend, task oracle and release criteria.

The fixed order is Pair 1: direct then compiled; Pair 2: compiled then direct. Four independent fresh fixtures are used. There are two observations per boundary in direct where the post-model generation must be revalidated; the compiled core obtains its observations through the standard public API. All observation/action calls, model turns, timestamps, usage records, fixture events/effect, readback and cleanup are retained.

## Gates and measurements

Each cell passes only with one completed initial model turn, coordinate in bounds, a generation-matched public observation after the model wait, one click-and-type action with confirmed release, a fresh observation after stage one, exact text visible before save, and a correct second decision for the direct arm. The compiled arm must produce the same local predicate and complete exactly two graph transitions without a second provider turn. Each then performs one save action, verifies retained release plus independent native all-up state, captures a fresh post-dispatch observation, and receives exact independent task-oracle success bound to the terminal action call, operation and generation. Fixture exit, AppServer close, and foreground restoration must pass.

Report paired differences for total elapsed time, AppServer time, turns, reported token fields, public observation/action calls, task correctness and cleanup. Preserve failed cells and do not replace them. AppServer journal usage is not independent upstream billing evidence; disclose missing image-token accounting. Two pairs are descriptive, not a causal estimate or reliability rate. No WSLc, Docker, MAP01, production application, energy, or OS/kernel input-hang claim is included.




