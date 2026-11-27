# R12 preregistration — live Win32 direct versus compiled efficiency

R12 is a fixed four-cell, counterbalanced, repeated task study on the authorized Windows PC. It does not change or replay R05–R11. Conditions and runner hashes must be frozen before the first fixture starts. Each cell gets a new fixture process, MCP session, AppServer planner session and independent oracle ID. Stop the series if a cell leaves unresolved input, an owned process, or foreground state; never replay an ambiguous action.

## Task and arms

Each cell begins from the same blank 400×180 owned fixture. The model selects a bounded click point from the public observation. Stage one clicks and types only `office`, making the application text visible while leaving it unsaved. Stage two saves and releases all inputs. The independent exact effect is `{saved:true,text:"office",clicked:true}`.

The direct arm asks the model again after a fresh post-stage-one screenshot whether the visible fixture state warrants saving. It then submits one standard public save action. The compiled arm runs a validated two-transition `run_public_compiled` graph: it observes the text/click state locally, then saves without a second model turn. Both arms use the same model, effort, initial prompt, coordinate bounds, fixture, action semantics, standard supervised Win32 backend, task oracle and release criteria.

The fixed order is Pair 1: direct then compiled; Pair 2: compiled then direct. Four independent fresh fixtures are used. There are two observations per boundary in direct where the post-model generation must be revalidated; the compiled core obtains its observations through the standard public API. All observation/action calls, model turns, timestamps, usage records, fixture events/effect, readback and cleanup are retained.

## Gates and measurements

Each cell passes only with one completed initial model turn, coordinate in bounds, a generation-matched public observation after the model wait, one click-and-type action with confirmed release, a fresh observation after stage one, exact text visible before save, and a correct second decision for the direct arm. The compiled arm must produce the same local predicate and complete exactly two graph transitions without a second provider turn. Each then performs one save action, verifies retained release plus independent native all-up state, captures a fresh post-dispatch observation, and receives exact independent task-oracle success bound to the terminal action call, operation and generation. Fixture exit, AppServer close, and foreground restoration must pass.

Report paired differences for total elapsed time, AppServer time, turns, reported token fields, public observation/action calls, task correctness and cleanup. Preserve failed cells and do not replace them. AppServer journal usage is not independent upstream billing evidence; disclose missing image-token accounting. Two pairs are descriptive, not a causal estimate or reliability rate. No WSLc, Docker, MAP01, production application, energy, or OS/kernel input-hang claim is included.
