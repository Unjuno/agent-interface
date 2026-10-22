# v39 health-feedback timing audit for Issue #59

This package independently recomputes a single retained trace from the frozen source commit in `FREEZE.json`. It is a posthoc audit of a previously consumed allocation, not a new live run.

## Result

At sequence 62, the retained typed-health signal changed from 97 to 85 during decision 1's pending model call. The authored health guard classified it `SOFT_CHANGED`, preserved the already-admitted cover policy, and granted no input authority. The monitor outcome was recorded **116.350 ms** after the observation's capture timestamp. The call ended **1,925.504 ms** after the signal.

The sequence-62 observation arrived during step 5's acknowledged `a` hold. The step completion record followed capture by **96.312 ms**. Step 6's `Down` and `space` input acknowledgement followed capture by **154.146 ms**. The cover program later ended with a verified-empty owner release **1,937.087 ms** after capture. These latter timings describe step and program boundaries only.

The retained event schema has no normal per-key key-up acknowledgement for this interval. The verified-empty owner release followed later input and is not a timestamp for when `a` was released. This package makes no per-key dwell claim.

Decision 1's pending action and decision 2's subsequent action were both rejected as not current. For decision 2, the authored action source was health 85 and the admission snapshot was health 73, failing its maximum-decrease predicate. The post-control score records one kill, zero deaths, no MAP01 exit, an unfinished episode, and reward 0. The run does not establish a verified positive task-effect onset, recovery benefit, or task success.

## Evidence classes and limits

**H (harness/report evidence):** hashes, event order, typed signal, monitor outcome, planner and admission status, owner release, and scorer fields are recomputed from frozen retained blobs by `audit.py`.

**T (timing):** durations are integer nanosecond differences converted to milliseconds. They are single-run timestamps, not distributions.

**D (visual description):** the accompanying manual frame note records a direct human review of the hash-pinned screenshots. It is not an OCR measurement and does not replace the typed-signal audit.

**C (causal claim):** none. This trace does not attribute the health loss or later action rejection to a causal performance benefit of the policy.

**U (unknown):** actual per-key key-up time, positive effect onset, counterfactual recovery, and matched-condition performance.

Run `python audit.py --write RESULT.json` to verify the frozen blobs and regenerate the result. Run `python -m unittest discover -s . -v` from this directory for the focused integrity and boundary tests.
