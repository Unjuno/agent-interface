## Successor preregistration — SAFE-DISCRIMINATING-OBSERVATION-6680-ORB-A01-20261003-01

The prior `HOLD_RESOURCE_BEFORE_FORMAL_START` record remains unchanged. This is a fresh allocation under the user's explicit direction to run the Issue experiment in OrbStack on macOS; it does not reuse or relabel the unconsumed prior allocation.

### H / T / D / C / U

- **H:** With identical preregistered pre-probe evidence, one admissible, bounded diagnostic observation identifies the correct recovery in the two identifiable synthetic worlds, reducing wrong recovery and post-recovery residual recurrence versus fixed reobserve and fixed reset, while mixed/ineligible/unsupported cases YIELD and release latency does not exceed immediate YIELD.
- **T:** Run the frozen v4 trajectory/predictor/timestamp/lease/effect fixture over all 5 cases × 4 policies (20 rows). Candidate sees only numeric fixture; hidden fault/effect truth stays in the separate oracle available to the independent auditor. Candidate and raw-only auditor run once each in separate containers, with no retry. Existing construction/negative-control outputs remain historical and are not pooled.
- **D:** `PASS_METHOD_SCOPED` only if candidate exits 0, independent audit reconstructs all 20 unique rows with zero errors, identifiable diagnostic actions match frozen correct recovery and beat both fixed baselines on wrong recovery and recurrence, mixed/ineligible/unsupported cases do not probe and YIELD, and all release/lease/budget/safety invariants hold. Candidate or audit nonzero, missing output, OOM, or disagreement is terminal STOP; do not retry. Any infrastructure failure before candidate invocation is recorded separately as STOP/hold, never as scientific FAIL.
- **C:** Fixed reobserve/reset or immediate YIELD may be simpler; fixture signatures/oracle may encode the answer; authored transitions may create the apparent effect.
- **U:** Finite deterministic synthetic method only—no real GUI, model, user data, natural fault rates, causality in live environments, or runtime/product safety claim.

### Frozen inputs and runtime

- Base: current `main` `c33380b3b08792a331ee11f7aee05e3d41437e3e`; additive branch `research/safe-discriminating-observation-6680-t0-20261002`, refreshed before this allocation. No formal output exists.
- Package: `research/analysis/safe_discriminating_observation_6680_t0_20261002/`; allocation outputs will be under `formal_a01_orbstack_20261003/`.
- Source SHA-256: temporal candidate `a2edee3964f28e2e9044e2a06f3acbb911ad0168a48f36f69e7522600d2157f4`; auditor `cb75345d519e9c32ac425a4f9785973a1779d032b01bbbf01b67d57dd6a6b2ef`; fixture `aaa3ff20a97f27489105d4c9125993eaf8f4c50c95cd2081f5487ccbef109ec8`; oracle `b735853126d38f37a4a62498e46ed89878fcc36727920aed87d74d4b3d043a23`.
- Dedicated OrbStack VM: `research-6680-a01-20261003`, Ubuntu 24.04 linux/arm64, 1 vCPU / 1536 MiB VM cap. Its separately installed Docker Engine is 29.1.3, cgroup v2; its inventory was empty before the run. This does not use or inspect the shared OrbStack engine or another task's VM.
- Container image: `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` (verified linux/arm64). Pull completed before allocation.
- Each candidate/auditor container: network none, 0.25 CPU, 256 MiB, 32 PIDs, read-only root and source, separate fresh output mount, UID/GID 1000, cap-drop ALL, no-new-privileges. Formal output directories are checked empty before launch.
- Invocation sequence: one candidate container writes `candidate.raw.json`; only on candidate exit 0, a distinct auditor container reads the raw and frozen oracle and writes `audit.json`. Preserve exact command, status, OOM state, raw outputs and hashes. Retries are zero.
