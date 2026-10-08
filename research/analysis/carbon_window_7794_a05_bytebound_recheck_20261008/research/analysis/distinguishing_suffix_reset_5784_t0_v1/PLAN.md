# Issue #5784 T0 plan — distinguishing suffix under suspect reset

## H / T / D / C / U

- **H:** A screenshot/seed match can coexist with history-dependent hidden carryover; an identical frozen suffix distinguishes it. Reset equivalence must use independent fresh-genesis anchors, not assume the candidate reset worked.
- **T0:** One local Docker/Linux x86_64 CPU-only finite fixture. Each arm begins at independently identified genesis; applies a distinct history, same candidate reset, then identical suffix. Include genesis→suffix reference, hidden carryover with semantically bad reset, known-bad reset positive control, clean reset, benign timing-only difference, and missing observation. Candidate emits raw rows once; a separately implemented auditor reconstructs expected cases and checks corruption controls. No GUI/model/GPU/network. One formal invocation, no retry.
- **D:** PASS_METHOD_SCOPED only if auditor detects both known semantic divergences, accepts clean reset and timing-only tolerance, classifies missing evidence UNKNOWN, and verifies independent genesis IDs. FAIL_METHOD on missed planted divergence or false acceptance from pixels alone. HOLD_NO_INDEPENDENT_START if genesis cannot be independently identified; UNKNOWN_SUFFIX if repeatability/tolerance cannot be established.
- **C:** Process/profile/filesystem recreation can itself be incomplete; the artificial machine is deterministic except explicit timing controls and does not prove GUI behavior. Fresh fixture recreation may dominate candidate-reset probing costs.
- **U:** Finite histories/suffixes may miss carryover; probes may perturb state; no finite PASS proves arbitrary application reset equivalence. No existing historical result is changed.

## New Issue correction incorporated

Issue #5784 comment 5924954442 corrects circular reset assumptions. Both experimental arms will originate from separate, independently hashed genesis manifests. Fixture assigns genesis identities outside candidate reset logic. Candidate reset is never the source of eligibility evidence.

## Frozen environment and allocation

- Allocation: distinguishing-suffix-reset-5784-t0-docker-20261001-01
- Base/main: 24da63015dc6d18f422bd92c1bcd435775fe3ff5
- Image: agent-interface-readiness-a3:local-20260927, observed image ID sha256:a89e10813abd763a71b88055d51737d5e827fe3b5e473a583156b65eef20105f
- Engine: Docker Desktop 29.8.0, Linux/amd64; Python 3.12.14, x86_64
- Limits: network none, 1 CPU, 256 MiB, 64 pids
- Invocation policy: candidate exactly once; independent auditor exactly once; no retries or post-outcome tuning.
- Formal source hash freeze: see FREEZE.json.

## Placement and delivery

Add only under research/analysis/distinguishing_suffix_reset_5784_t0_v1/. Retain plan, freeze, candidate, independent audit, immutable raw, report, execution transcript and hashes. Update corresponding Issue and deliver by reviewable PR. Do not alter shared runtime, global roadmap, previous results, or old issues.
