# A08 frozen run contract

- Allocation: `5309-WITNESS-A08-ORBSTACK-20261007`; successor to A06 method failure and A07 pre-start STOP, not a retry.
- Issue: #5309. Exact main SHA: `3dba6c86f212c37a2d80c844b816c38921a42cc5`.
- **H:** Given equal predicted information gain and identical admissible actions, generic IG chooses the first lexical action. Its state-identifying receipt cannot replace a lost independent effect receipt; witness-aware selection chooses the equal-cost action predicted to preserve it and completes only if the receipt is actually observed.
- **T:** Two opaque receipt cases × seven scenarios × four arms = 56 rows. Candidate sees only candidate code, candidate-input, model and case observation profiles; no oracle file or hidden-state labels are mounted. Auditor sees candidate input/raw and a separate oracle mount; candidate code is absent. Both roots read-only, only output dir writable, network disabled, 1 CPU/256 MiB, no extra capabilities, pinned linux/arm64 Python image.
- **D:** PASS only if independent audit reconstructs all 56 rows and correct true commit/effect pairs; both compared arms have the same admitted set; primary generic is `UNKNOWN_EFFECT_WITNESS_LOST` and witness-aware is `COMPLETE`; no-path/stale/model mismatch remain UNKNOWN; duplicate ID consumed once; urgent-stop releases before commit; zero authority; six corruption probes rejected. Any deviation is retained without retry.
- **C:** A mandatory effect readback, pre-existing witness, better model, or banning generic-IG task selection could remove the contrast. Finite authored dynamics may favor witness-aware behavior.
- **U:** Synthetic method-isolation only; no natural frequency, GUI/model/runtime/product benefit, user performance, safety or physical-release claim.
- Image: `python@sha256:c845af9399020c7e562969a13689e929074a10fd057acd1b1fad06a2fb068e97`, linux/arm64.
- Exact formal commands (also smoke-tested before freeze):

```sh
sh research/analysis/dual_control_5309_witness_a08_20261007/run_candidate.sh
sh research/analysis/dual_control_5309_witness_a08_20261007/run_auditor.sh
```

Candidate, input, oracle, auditor, tests, launchers and this contract are frozen by SHA-256 in the A08 Issue comment. Recheck hashes, main, image digest, successful smoke gates and no pre-existing A08 containers immediately before formal execution. One candidate run, then one auditor run, zero retries.
