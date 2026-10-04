# A04 execution record

- Freeze: PRE-RUN.json, 2026-10-04T06:24:00Z; base main bbed04b9bf5ad7d94e20fcea212b98d19dfa6395; one candidate run, no retry.
- H/T/D/C/U: as frozen in PRE-RUN.json.
- Collision check: no remote branch or open PR matching 7424-a04-pareto before invocation. Existing A02 evidence is merged; A03 PR #7500 is a distinct open successor whose saved cold route is the comparator.
- Runtime: Ubuntu WSL2, Python 3.12, ext4 worktree. Docker Desktop was not reachable from this distro (no /var/run/docker.sock); no image pull or container launch was attempted. The deterministic finite CPU construction ran directly on the local computer. No WSLc, game, GUI, model, input, or external allocation.
- Candidate invocation: python3 run_a04.py --raw raw.json; exit 0, one invocation.
- Candidate result: both eligible cases have cold first jump 0.20 and continuity-bounded oracle jump 0.15, a 25% reduction. The no-disturbance oracle IAE is 2.693287601396 versus pinned A03 cold IAE 6.023787768676; step-disturbance oracle IAE is 2.294238964978 versus pinned A03 cold IAE 5.646697966151. The oracle is an upper-envelope reference-tracking sequence, not a demonstrated controller implementation.
- Audit history: first audit exited 1 because the independent checker compared the exact step-case replay value against the README-rounded 5.65 at a tolerance of 0.00005. The pinned A03 raw records 5.646697966151. The failed output remains in AUDIT_OUTPUT.txt. A rounding-tolerant audit pass is retained separately. A later exact source-trace cross-check matched both full 20-command cold routes and their IAE values to the pinned A03 raw blob. The final source-pinned audit and five tests pass. The candidate was not rerun.
- Disposition: the preregistered infeasibility hypothesis is falsified for these two scalar cases; the envelope demonstrates a feasible point on the bounded plant's continuity/tracking frontier. No conclusion about live controller-state conditioning, safety, or task effect follows.
- U: no nonlinear/discontinuous plant, authority handoff, physical actuator, real task, useful-feedback measure, or end-to-end integration was tested.
