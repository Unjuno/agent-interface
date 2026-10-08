# Issue #8544 T0 A01 — candidate launch STOP

**Disposition:** `STOP_CANDIDATE_LOG_REDIRECTION`; no candidate or auditor process ran, and no retry is permitted.

The first frozen candidate command was issued after writing its start receipt to `results/candidate.start.utc`, but the package's `results/` directory did not exist. The shell could not open the receipt and stdout/stderr redirection paths:

```
zsh:2: no such file or directory: research/analysis/crowding_target_flanker_8544_t0_20261009/results/candidate.start.utc
zsh:3: no such file or directory: research/analysis/crowding_target_flanker_8544_t0_20261009/results/candidate.stdout.txt
zsh:4: no such file or directory: research/analysis/crowding_target_flanker_8544_t0_20261009/results/candidate.end.utc
zsh:4: no such file or directory: research/analysis/crowding_target_flanker_8544_t0_20261009/results/candidate.exit
zsh:4: no such file or directory: research/analysis/crowding_target_flanker_8544_t0_20261009/results/candidate.sha256
```

The candidate Python process therefore did not start; no raw output, stdout/stderr files, or formal output hash exist. Candidate command attempt count: 1; Python candidate process count: 0; auditor process count: 0; retries: 0. The gate requires a successful candidate output before auditor execution. This is an execution/custody STOP, not a scientific result and not evidence for or against the Issue's hypothesis. Construction tests and the separate temporary-file replay remain construction-only evidence.

The formal failure is retained additively. No candidate rerun, auditor run, or model call is authorized by this allocation.
