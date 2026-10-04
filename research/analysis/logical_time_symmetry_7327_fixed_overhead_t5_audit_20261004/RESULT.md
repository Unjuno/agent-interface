# T5 audit-only result — PASS_FIXED_OVERHEAD_DISTINGUISHED

The T5 independent auditor ran once and exited 0. It reconstructed all three rows in the immutable T4 raw from the frozen exact-rational spec and source identity; integrity errors=0 and mutation controls rejected=4/4.

All preregistered checks passed:

- Factor-2 homogeneous normalized observation traces are equal for all three scenarios.
- The zero-startup fixed-delay control is unchanged.
- On the reachable hazard case, the homogeneous first unsafe observation remains at normalized time `1/4`; leaving the nonzero `1/4` startup delay fixed moves it to normalized time `9/8`.
- The quiet nonzero-startup fixture confirms the representation remains explicitly bounded to this observation/event model.

T4 remains a retained STOP: its candidate ran once/exit 0 and wrote the exact raw now audited here; its auditor ran once/exit 1 in mutation-control code before output. Neither T4 command was rerun. T3 remains a separate zero-invocation `STOP_MAIN_ADVANCED_BEFORE_CANDIDATE`.

This is a scoped synthetic-method finding only. It shows the fixture distinguishes a nonzero absolute startup delay from homogeneous scaling; it does not establish that any real controller has this delay, that physical time scales homogeneously, or any GUI/MAP01, safety, task-effect, latency, or product result. OrbStack was not used because Engine inventory fails on a containerd blob; no image pull, launch, or retry occurred.

Validation: T5 preflight 3/3; formal audit once/exit 0; T4 raw/source/spec SHA binding verified; `output/audit.json` SHA-256 `5a2ab3ec3a1e80bfb494ce7149c9a2489c6b8c703aed89de0f601416fbc12088`.
