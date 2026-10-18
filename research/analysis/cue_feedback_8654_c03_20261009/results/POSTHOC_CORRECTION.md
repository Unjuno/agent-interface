# C03 post-freeze STOP correction

This additive record preserves the C03 source freeze and does not edit its PREREG.md, scripts, or workflow.

The frozen branch is research/8654-c03-support-sufficiency-20261009, but the workflow's push.branches entry is research/8654-c03-raw-custody-20261009. The GitHub Actions collection contains create-event jobs on the new branch but no push run for the C03 workflow. Those create-event jobs are not candidate/auditor invocations. Candidate, raw artifact upload, and auditor counts are all zero. No scientific result exists.

C04 will use a distinct branch/path/source freeze. Its pre-publication check requires exact equality between the proposed branch and the workflow branch filter. C03 will not be rerun or relabeled.
