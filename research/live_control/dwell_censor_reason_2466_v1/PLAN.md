# Issue #2279/#2466 informative-censoring rung

## H
A single generic right-censor bucket is insufficient when censor cause changes whether a later action is still valid. In two private live application-like dwell families, focus loss, owner death, an unverified upper bound, and an observed bound violation should remain typed HOLD conditions. A cause-aware caller that re-observes at finite M and refuses invalid/unknown state should avoid the unsafe PROCEED decisions exposed by a generic-censor control while preserving normal and within-M delayed positives.

## T
Two families: TK_CALLBACK (effect observed from live Tk widget state) and WORKER_FILE (separate worker completion observed by a Tk file watcher). Six schedules: NORMAL, HORIZON_LATE, FOCUS_LOSS, OWNER_DEATH, BOUND_VIOLATION, UNKNOWN_BOUND. Two policies x two repetitions = 48 fresh processes on one private Xvfb. Horizon=100ms; finite M=220ms except UNKNOWN_BOUND. No model/provider/network/user desktop. Candidate gets typed censor reason, evidence/session identity, monotonic clock and M provenance. Generic control deliberately collapses causes. Application-like NEXT effect occurs only after policy PROCEED; independent audit scores whether effect_done + owner_alive + focus_target held immediately before PROCEED.

Construction: source/unit checks plus one nonformal case per family/policy only. Formal: one invocation, no retry/replacement/tuning. All rows, process exits, raw event brackets and private Xvfb cleanup retained.

## D
PASS_CENSOR_REASON_BOUNDARY_SCOPED only if all48 rows and identities reconcile; CAUSE_AWARE proceeds all NORMAL/HORIZON_LATE cells and holds all FOCUS_LOSS/OWNER_DEATH/BOUND_VIOLATION/UNKNOWN_BOUND cells with zero unsafe proceeds; GENERIC_CENSOR proceeds all cells and exposes exactly16 unsafe proceeds (2 families x2 reps x4 unsafe scenarios). Raw-only independent audit must pass and six corruption/unit controls reject. Complete contrary behavior is FAIL; missing source/process/denominator is STOP/HOLD.

## C
This is a directed fixture, not a natural censor-frequency estimate. Focus and owner transitions are explicitly scheduled. Generic policy is an authored unsafe comparator, not claimed production behavior. The application NEXT effect is fixture-owned and not OS input authority. A finite M is diagnostic and not calibrated from a deployment population.

## U
No rich-model decision, token accounting, empirical M calibration, third held-out surface, production GUI, physical input, power loss, arbitrary focus manager/toolkit, hard-real-time guarantee or human-tempo claim. Broad #2279/#2466 and global ROADMAP remain open.
