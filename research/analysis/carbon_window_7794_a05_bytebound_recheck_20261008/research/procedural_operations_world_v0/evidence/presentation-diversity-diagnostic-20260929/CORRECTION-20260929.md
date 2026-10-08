# Successor correction and Docker reproduction (2026-09-29)

This file supplements, and does not rewrite, the evidence merged in PR #5238.
The original `variation_audit.c` and its reported `0/190` stride comparison
are retained as historical artifacts, but that comparison is invalid and must
not be cited as a result.

## Review defect and correction

The original helper rendered the current world with `target_complete=0`, but
did not reset `target_complete` on each prior-family world after replacing its
task mask. For original task graphs without the target task, initialization
could leave that field set, producing mismatched cue visibility. The reviewer
finding is valid. The original `0/190` stride-97 comparison is withdrawn.

`variation_audit_corrected.c` prepares every rendered world through the same
function, including the task mask, dependencies, completion state, active
target, and actual presentation-family identity. The stride comparison only
counts unordered pairs with distinct actual presentation families, rather
than requested keys that alias to one generated family.

## Reproduction and result

- Frozen source commit: `1314d8d0113fcef1b72694e6ca0431b5420f74c5`.
- Compiler: WSL2 Arch Linux, GCC 16.1.1, static, `-O2 -std=c11 -Wall -Wextra -Wpedantic`.
- Docker: cached `debian:bookworm-slim@sha256:3783cc01769c7b2b1b83a5c5ad96c815348e28ed7da68e2e3687004faa906251`, `linux/amd64`, `--pull=never`, `--network none`, read-only root and bind mount, 1 CPU, 512 MiB, 32 PIDs, dropped capabilities, `no-new-privileges`, disposable `--rm`.
- Source was compiled on WSL and not mounted into the container; the static test and corrected-audit binaries were mounted read-only.
- Docker exit code: 0. Existing suite: `20/20 validity-hardening tests PASS`.
- Corrected diagnostic: 5,120 combinations; all 12 actual presentation families and all four cue modes observed; zero full-frame hash collisions between distinct actual families; one requested-key alias (seed 57, keys 2 and 11, actual family 2).
- Sample seed 234: 20/20 unique full-frame hashes; stride-97 comparison has 177 distinct-actual-family unordered pairs and 0 collisions. The other 13 of 190 requested-key pairs alias to the same actual family and are excluded from the cross-family comparison.

Static binary SHA-256 values:

```text
test_ops_world          0498d214d71dfb7a79598a4db0d901dbd981b45321c6966630c45e3957f45d6f
variation_audit_corrected 1d889396a551df8c1b26f698332e47770043e8fc87eea2b4e497eda9fd0514b9
```

The container was an isolated local one-shot experiment. The pre-existing
`mitra4821-ast-parse-01` container was left untouched and remained running.
No workflow, GPU, model/provider, GUI/X11, input dispatch, or scored episode
was used. This remains construction-only evidence and does not resolve the
formal HOLD on Issue #5206.
