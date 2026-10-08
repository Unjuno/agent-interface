# Issue #5323 — first-unit result

Allocation `causal-attribution-5323-t0-20260930-01` ran once in OrbStack on
2026-09-30. The frozen input was eight synthetic event traces; five policies
produced 40 rows. No model, network, GUI, input, or external effect was used.

## Result

The independent raw-only audit reports `PASS_AUDIT`, 40 rows, and no errors.
False `CAUSAL_EFFECT_IDENTIFIED` claims by policy were:

| Policy | False identifications | Missed known action causes | UNKNOWN |
|---|---:|---:|---:|
| POSTHOC_ASSOCIATION | 5 | 0 | 0 |
| TEMPORAL_LINEAGE | 1 | 0 | 5 |
| CONTROL_BASELINE | 0 | 1 | 6 |
| CAUSAL_MODEL | 0 | 0 | 6 |
| UNKNOWN_ON_CONFOUNDING | 0 | 0 | 6 |

`CONTROL_BASELINE` retains an effect link under declared control assumptions,
not causal identification; it is counted as a miss only under the stricter
identified-status metric. `CAUSAL_MODEL` receives a complete-graph flag and
synthetic truth labels, making it an oracle comparator rather than a realistic
inference algorithm. `UNKNOWN_ON_CONFOUNDING` retains the clean direct-effect
case while refusing attribution in six ambiguous/unidentified cases.

## H/T/D/C/U

- **H:** Explicitly separating association, effect linkage, causal identification,
  and `UNKNOWN` can reduce false causal claims under known/hidden competing
  causes without suppressing a clean direct effect.
- **T:** The frozen eight-case × five-policy finite matrix in `cases.json` was
  executed in a network-disabled, source-read-only container; `audit.py` in a
  separate container independently recomputed expected statuses and metrics.
- **D:** Scoped first-unit gate met: complete 40-row matrix; case SHA matched;
  independent oracle errors 0; posthoc negative control produced false claims;
  conservative gate produced 0 false identified claims and did not miss the
  clean direct effect. Decision: `PASS_FIRST_UNIT_SCOPED`.
- **C:** Synthetic authored traces only. The idealized causal-model policy uses
  supplied truth/completeness labels. Baseline and lineage assumptions are
  stipulated, not empirically established. This is not a runtime implementation.
- **U:** No graph-completeness, confounder-prevalence, calibration, latency,
  cost, UI, task-success, authority, or production-safety claim follows.

## Execution provenance and deviations

- Base main: `cf8ad3d1a675af9e64c1be356d03e35699548b33`.
- Container: OrbStack Docker Engine 29.4.0, `linux/arm64`, image
  `python@sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b`.
- Runner: one invocation, exit 0. Raw SHA-256:
  `1cd99c857eb5d0c488cf9a0c7b6abd1cf634693500cb5490c18acc4d0c856b09`.
- Auditor: separate container invocation emitted the retained
  `PASS_AUDIT` JSON. The host wrapper then errored assigning zsh's reserved
  readonly variable `status`, so the Docker exit code was not captured; no
  retry was made. Audit JSON SHA-256:
  `c7ab944645c1576ab77a88563a10eda77da8e21228a47b2b34b0b1e61ec1246e`.
- A first local test command used repository-root cwd and failed to import the
  package test; the corrected focused run from this directory passed 7/7.
  These command errors do not alter the frozen input or raw experiment.
- `py_compile` passed and `git diff --check` was clean after the corrected run.
- The repository analysis-index checker was invoked but cannot give a valid
  full-tree answer from this sparse checkout (existing indexed result folders
  are omitted). The generated index was updated with the new sorted entry;
  no destructive `--write` was run. The PR's full-checkout Analysis Index job
  must verify it.

See `EXECUTION.json` for commands, counts, hashes, and exact recorded
limitations. Prior experiment bundles remain untouched.
