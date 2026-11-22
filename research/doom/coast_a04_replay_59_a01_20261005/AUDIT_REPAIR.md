# Raw-only audit harness repair

The first separate-process candidate/auditor comparison exited successfully in both processes but exact JSON comparison failed because the auditor omitted `baseline_sequence`, which the candidate output included. The initial raw output files were not retained. Inspection showed that predicate values, first trigger rows, and counts matched; only the output schema differed.

The auditor was corrected to emit the selected baseline sequence. A single subsequent comparison of separate candidate and raw-only auditor processes exited 0/0 and matched all five result objects exactly. This repairs the audit harness and does not change the post-hoc freeze failure or reclassify the trace result.

