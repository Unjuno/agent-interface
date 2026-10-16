# D03 imposed sibling-load sleep experiment

Existing Issue #6067; additive successor of D02 HOLD, not its replay. Main intake b3b42b23833085968090975498c313fff3fb1fce; canonical README/ROADMAP/CURRENT_GOAL unchanged. PR7035 sleep/spin diagnostic remains separate. Open/closed Issues, PRs, branches and parent history checked. Existing isolated worktree reused; unrelated wslc_smoke.sh edit preserved.

## H/T/D/C/U

H: under fixed CPU1, two controlled sibling burners increase pure-sleep wake lateness versus zero burners and produce leaf CPU throttling. This tests an imposed resource-load mechanism; NOT whether quota caused A03/D02.
T:12cells/6pairs, order quiet-loaded / loaded-quiet / loaded-quiet / quiet-loaded / quiet-loaded / loaded-quiet. Each16absolute40ms-spaced deadlines, initial200ms after100ms settle. Same sequential parent and cgroup, no spin, GUI, input, model or GPU. Burners send typed child PID readiness, then bounded computation, require parent stop and terminal0. One producer block, first invalid cell STOP, partial evidence retained, retries0. One saved-only audit after complete terminal0.
D: support only when pooled median loaded-minus-quiet>=1000000ns, >=5of6 paired median differences>=1000000ns, and all6loaded cells show positive nr_throttled and throttled_usec delta. Otherwise HOLD_NOT_SUPPORTED. Complete budgets/lifecycle/source/counter/clock/resource gates required; malformed data STOP. Raw timing failures remain outcomes, not exclusion. Quiet throttling need not be zero; report it.
C: added runnable work changes runqueue contention AND quota pressure; it is not a pure quota-only intervention. Serial balanced order cannot remove shared host, carryover or cgroup-period phase confounds. Short run may not reproduce rare tails.
U: sleep bracket wall-minus-process CPU is not descheduling. /proc/self/schedstat may be unavailable or disabled; preserve status/raw, do not substitute zero for measured scheduling delay. Counter snapshots surround sleep plus their own read overhead, not exact causal syscall attribution. No rootcause, pacing repair, GUI detection/phase, safety, task efficacy, hard-real-time or roadmap completion claim.

## Resources / ownership

Only private VM research-6183-t0-20261003 UUID01M3ZD3J2GK283SQRFW9EW9DBZ, idle own Engine. Cached arm64 image sha256:c4839671ed0625dd38a53d8ed542bab16407c2b4c88a5ac84431695438c2b816. CPU1/512MiB/swap0/PIDs64/nonroot501:501/networknone/read-only root and source/capdropALL/no-new-privileges/tmpfs64MiB; actual cpu.max/memory.max/swap.max/pids.max read inside container. No shared VM, physical-host exclusivity or ancestor-limit absence claim. No installs/network in experiment. Explicit python command replaces image default setup Cmd.

Operator preflight mistakes before any acquisition: one image ID typo, one Go-template missing Entrypoint key, host /proc/sys/kernel/sched_schedstats absent. These were inspection errors, not formal outcomes. Actual container runtime and optional scheduler availability will be retained independently.

Frozen source and commands precede producer launch. Source, raw, auditor and inspection hashes retained. Independent source/raw review and applicable unchanged CI required before PR/main. Retain first STOP and old evidence unchanged. Broad repository tests that may invoke consumed native studies are not authorized; only method tests and applicable CI are claimed.
