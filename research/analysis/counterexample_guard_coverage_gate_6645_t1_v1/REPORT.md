# Issue #6645 T1 — hidden-family coverage-gate challenge

## Result

`PASS_COVERAGE_GATE_SCOPED` for the frozen five-row synthetic finite fixture.
The separate candidate and raw-only auditor ran once each in pinned OrbStack
containers, both exit 0, with no retries. The independent auditor reconstructed
all five decisions from the frozen contract, fixture, and candidate raw output;
it reported zero errors.

The coverage-blind comparator admitted the harmful modal-occlusion case because
its two observed features matched the safe control. The tested gate saw that
`modal_occlusion` was required by the independent frozen contract but missing
from that candidate row's covered-family declaration, and returned UNKNOWN.
It also returned UNKNOWN for the explicitly unregistered family. With declared
coverage complete, it admitted the valid control and refused the known stale
target control.

## Interpretation

This advances the exact residual named by Issue #6645: a registered hidden
family can defeat seen-feature-only generalization, while an explicit
coverage-completeness obligation can prevent that case from becoming a false
PASS. The result is not a rerun of the earlier WSLc T0 or its later OrbStack
replication; it tests only the coverage-gate boundary with a new frozen fixture
and different decision criterion.

## Scope and limitations

The result depends on an externally supplied family registry and an authored
assertion that it is complete for this fixture. The experiment does **not** show
how to discover a wholly unknown, unregistered safety dimension, prove that a
real predicate ontology is complete, or establish behavior of live skill caches,
GUI applications, users, models, or product safety. An uninstrumented unknown
dimension cannot be detected merely by a finite run that omits it. The gate's
coverage-blind comparator is intentionally weak and is not a production
baseline. `memory=512 MiB` and `memorySwap=1 GiB` are requested Docker settings,
not evidence of host/cgroup enforcement or memory-pressure behavior.

## Reproduction

Read `FREEZE.json`, verify `FREEZE.sha256`, then follow `RUN_COMMANDS.md`.
First-outcome raw evidence, audits, container inspections, source/image identity,
invocation counts, and output hashes are retained alongside this report.
