# Successor #4908 — role-separated online LoRA skill retention

## H / T / D / C / U

### H — hypothesis
A fail-closed role router with an immutable A skill and a distinct online B LoRA skill will retain A while acquiring B corrections, while routing both roles through one shared adapter will forget more A. Fixed A-replay is a descriptive comparator because it changes batch shape and objective.

### T — frozen experiment
- Allocation `needle-role-skill-joint-retention-20260928-v1`, issue #4908, branch `research/needle-role-skill-joint-retention-v2-20260928`, path `research/system1/needle_role_skill_joint_retention_v2/`.
- Construction-only excluded seed 736514. Formal seeds 736711, 736811, 736911 remain unspent; no formal fit is authorized by this construction run.
- 9-input, 16-hidden, 4-logit task; explicit role bit; disjoint A base 256, A memory 16, B support 16 and held-out A/B 256 each. A base uses 400 single-row AdamW updates. Four arms use 16 arrivals × 8 adapter updates. Three invalid-route controls yield without selection or proposal.
- Fixed cached `linux/amd64` CPU image `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`; Docker pull disabled, network disabled, source read-only, 1 CPU, 2 GiB, 64 pids. GPU is intentionally unused because this exact registered task is CPU-only and tiny; moving it to CUDA would change the execution condition.
- Hash contract has exactly 11 named data/label/schedule fields, including `base_row_indices`. Construction requires exact key-set and digest coverage; auditor regenerates the schedule and data independently. Each arm is reconstructed independently; no cross-arm bit-exact claim.

### D — decisions
- `PASS_CONSTRUCTION_AUDIT` only if the excluded seed's raw is independently regenerated and all source/data/schedule hashes, optimizer states, predictions, route receipts, immutable A state, YIELD controls, and update timings pass with zero audit errors.
- `HOLD_AUDIT_INTEGRITY` for any reconstruction, provenance, schema, or audit defect. This takes precedence over descriptive quality.
- `STOP_*` for missing image, source mismatch, output collision, or pre-fit environment failure. This construction result cannot establish the three-seed hypothesis or authorize a formal fit.

### C — alternatives and confounders
Adapter isolation changes parameter capacity and optimizer state as well as routing. Replay changes objective and batch shape. The explicit role is supplied, not inferred. Arm trajectories are audited independently.

### U — limits
One excluded seed on one local CPU image, tiny synthetic model and explicit role bit. No natural-language routing, live Needle utility, broad transfer, production online learning, safety, action authority, GPU benefit, or user outcome.

