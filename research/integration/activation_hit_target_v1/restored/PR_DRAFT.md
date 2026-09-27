# UNPOSTED PR draft — research: separate activation hit target from keyboard recipient

Add only `research/integration/activation_hit_target_v1/**`. Preserve #4036/PR #4053 and all old allocations; close no broad parent.

Retrospective delivery of one locally preregistered native experiment, not public preregistration. The 26-case/3-batch allocation passed its frozen boundary gates; 3,094 independent raw checks, 12/12 evidence mutations and seven policy tests pass. All actual app/server/runner exits are zero. Native backend blob is exact; only an unused manifest import is omitted during research loading.

Main result: checking focus AFTER a recovery click stops wrong text but can leave a committed collateral Button effect. Checking the native hit child BEFORE the click protects already-occluded targets but still does not solve the after-check interval. Do not label the candidate generically safe. Include all four construction attempts, including the authentication STOP; no formal rerun or result rewriting.

Delivery patch is additive and scratch-application-tested, but upstream repository CI/review has not run. Before merging, verify target path collision, source/evidence hashes, current-head checks and compatibility with the result/recovery spine. No shared runtime/default change is proposed. Remove only the newly owned branch after a verified merge and dependency review, using supported tooling. This document is not evidence that a PR exists.
