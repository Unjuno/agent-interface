# Finish pipe pressure 01

Disposition: FAIL_FINISH_PRESSURE_REACHABILITY_SCOPED.

One frozen WSLc construction uses literal main cleanup source and a real Python child that does not read stdin. Filling 65,536 bytes exhausted the pipe. At the fixed 0.5-second observation, cleanup remained alive, no child.wait had started, planner.close had not run, and the primary exception had not returned. A separately owned probe then killed its direct child. Cleanup subsequently returned the original ValueError and closed the fake planner.

This establishes a concrete preceding synchronous write/flush reachability gap; wait(timeout=5) does not bound it. Probe kill is external rescue, not controller cleanup. No game, model, physical input, scorer closure, descendants, universal deadline or task recovery was tested. The harness assertions passing confirm the counterexample, not the cleanup contract passing. Requested memory is limited without swap according to the retained kernel warning.

H/T/D/C/U was prospective in Issue #59 comment 5979102687; result comment 5979143797. Preserve this first outcome and source bytes. Any repair must have a separate frozen construction. Peer PRs #7584 and #7586 have distinct classification/source-stop scopes. Full roadmap remains open.
