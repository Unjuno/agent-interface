# Formal orchestration incident before case 07 instantiation

After formal cases 0–6 completed, the outer wrapper attempted scheduled case 07 without the frozen runner's required `--case-id` argument. `argparse` exited with rc=2 before `run_case.py` created the scheduled case output directory, started Xorg/inputtest, or emitted task input/result data. The incident was posted to Issue #655 before case 07's first actual instantiation.

The wrapper's first raw `case-07...stdout/stderr` sidecars were later overwritten by the successful actual case-07 wrapper invocation. Therefore this file is a post-incident reconstruction from the observed tool output and GitHub comment, **not a claim that the original raw stderr file is retained**. Known stderr included: `run_case.py: error: the following arguments are required: --case-id`.

No experiment source, schedule, case semantics, thresholds or auditor changed. Case 07 itself had no prior case directory/result and was instantiated once after the wrapper syntax was corrected.
