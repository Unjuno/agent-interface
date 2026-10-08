# Issue #8397 T0 A02 — frozen finite-trace protocol

## H / T / D / C / U

**H.** In a deterministic finite trace fixture for a fixed policy, observation omission has state- and interval-dependent effects: at least one preselected interval preserves exact task effect while reducing model-visible calls/bytes; an interval crossing a task-relevant transition causes task-effect regret or recovery; an interval after an independently verified terminal effect can reduce optional model-visible cost without changing the effect.

**T.** Enumerate one baseline and one omission arm for each of `pre_decision`, `cross_transition`, and `post_completion`, plus a `captured_undelivered` transport control and a `mandatory_safety` rejection control. There are exactly eight records. Every record carries interval membership, captures, deliveries, model-visible bytes, mandatory-cue status, decision, exact task-effect label, recovery steps, and stop outcome. The raw-only auditor independently enumerates the expected eight records, exact costs/effects/outcomes, and all case membership. No model, GUI, OS input, user data, live application, or external effect is involved.

**D.** `PASS_METHOD_SCOPED` only if the raw-only audit reconstructs all eight exact records; distinguishes capture from delivery and withheld observations; confirms the pre-decision and post-completion arms preserve the exact effect while lowering delivered calls/model-visible bytes; detects the cross-transition wrong-target effect and recovery; and rejects any route that omits the mandatory safety cue. Any mismatch is `FAIL` and preserved. This only tests the authored finite trace contract.

**C.** These cases are hand-authored and may overstate how often GUI tasks have harmless or observation-sensitive intervals. The trace labels are not an independent real application oracle.

**U.** No result about a live policy, screenshots, GUI, model behavior, user-visible safety, timing, or transfer to other tasks. The single synthetic fixture cannot quantify rare risk.

## Environment and execution choice

The current Issue defines T0 as a small finite CPU fixture; its stated T0 does not require container behavior. OrbStack context was `orbstack`; `docker ps` succeeded but image metadata inspection/listing failed with a containerd content-store `operation not supported` error. The host data volume showed 146 GiB available and 97% used. No container pull/build, daemon repair/restart, cleanup, or host-level network change was attempted. To avoid treating that infrastructure failure as a scientific outcome, A02 uses native macOS CPython under `sandbox-exec` with `(deny network*)`. This is a CPU method-fixture run, **not** a Docker/OrbStack/container reproduction and makes no isolation/resource-cap claim beyond the process network deny rule.

## Frozen execution commands

Run from the repository root, in order, once each, with no retries:

1. `sandbox-exec -p '(version 1) (allow default) (deny network*)' python3 research/analysis/observation_omission_regret_8397_t0_a02_20261008/candidate.py --output research/analysis/observation_omission_regret_8397_t0_a02_20261008/results/FORMAL_A02/candidate.json > research/analysis/observation_omission_regret_8397_t0_a02_20261008/results/FORMAL_A02/candidate.stdout.txt`
2. `sandbox-exec -p '(version 1) (allow default) (deny network*)' python3 research/analysis/observation_omission_regret_8397_t0_a02_20261008/auditor.py research/analysis/observation_omission_regret_8397_t0_a02_20261008/results/FORMAL_A02/candidate.json --output research/analysis/observation_omission_regret_8397_t0_a02_20261008/results/FORMAL_A02/audit.json > research/analysis/observation_omission_regret_8397_t0_a02_20261008/results/FORMAL_A02/auditor.stdout.txt`

The candidate and auditor create their JSON files exclusively (`open(..., "x")`). Construction tests are separate and have already completed before freeze. At freeze time formal candidate/auditor counts are 0/0, retries 0.
