# A02 source-mutation negative control

This is an additive posthoc control. It does not modify or rerun the frozen A02 candidate, source, or raw evidence.

## Mutation

In a copied `controller_source.py`, only the two `grants_input_authority: False` literals inside `DoomCoverSignalPairMonitor._invalidation` were changed to `True`: both the default outcome and the top-level invalidation receipt. The copied A02 `candidate.py` and `audit.py` were unchanged. The retained source slice and literal count were checked before writing the mutant.

## Result

- Candidate ran with CPython 3.11.9 and reported 2/9 cases passing, then exited 1. The two explicit hard-floor outcomes passed; cases using the default invalidation output failed closed-outcome expectations.
- Independent audit rejected the resulting raw and exited 1. It reported top-level authority grants for six cases and outcome authority grants for five cases (the hard-floor cases supply their own outcome), for 11 rejected field observations.
- Mutant source SHA-256: `296483811c3b95beb408cd572c86ac3fbde9dae59f11a6b4508e69b3ffd21d26`.
- Raw retains the mutant source hash and candidate outcomes. `CONTROL.log` captures both exit codes and the exact replacement count.

## Environment limit

The prior retained A02 run used WSLc, `python:3.12-slim`, network disabled, 1 CPU, and 512 MiB; its cgroup/swap warning remains in A02 `RUN.log`. In this session `wsl -d WSLc` returned `WSL_E_DISTRO_NOT_FOUND`; only `archlinux` was registered, and neither Docker nor Podman was available. This posthoc control therefore ran natively under CPython 3.11.9. It is supplemental source-mutation evidence, not a reproduction of the frozen WSLc run.

No live game, real input, planner, producer integration, or task outcome was exercised.

