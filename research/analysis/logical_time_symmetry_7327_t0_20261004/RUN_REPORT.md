# T0 result — logical-time symmetry (scoped method result)

Allocation: LOGICAL-TIME-SYMMETRY-7327-T0-20261004-01  
Preregistration: Issue #7327 comment 5974956400  
Frozen provenance main: 4d42238694c55aaa29bf47cb13a5b8d4c5d4074a  
Frozen source branch tip: 0704cf47a14e8160279f859de9f1d11c8931be30

## H / T / D / C / U

- **H:** For a fully declared homogeneous logical-time fixture, unit representation changes and uniform scaling preserve normalized observable traces; leaving a reachable lease boundary fixed is distinguishable.
- **T:** Six exact-rational event schedules were executed once in a no-network WSLc container. A separately invoked raw-only auditor reconstructed all rows and ran four corruption controls.
- **D:** **PASS_LOGICAL_TIME_SYMMETRY_SCOPED for the frozen allocation subset.** Candidate exit 0; auditor exit 0; 6/6 cases reconstructed; exact unit-representation traces; normalized traces equal for all 18 homogeneous factor/case pairs; four of four mutation controls rejected. The fixed lease changed the normalized trace in the null case where lease expiry was the active boundary, and did not change the other five cases because an earlier observed state change triggered release. Keeping a zero startup delay fixed did not change any trace.
- **C:** This supports only the declared finite simulator relation. It does not show a real system is homogeneous; an unmodeled absolute delay, quantization, asynchronous backend, or omitted variable may break the relation.
- **U / coverage qualification:** This allocation did not test a nonzero fixed backend/startup delay, nonzero clock quantum, or physical/semantic rate transformation. Therefore it does **not** complete every proposed T dimension in Issue #7327 and does not validate the full disturbance-time model. The result is a narrow method PASS, not a live-control or accelerated-time equivalence claim. Preserve this first result; do not expand or rerun it in place.

## Execution

Candidate invocation: 1, WSLc exit 0.  
Independent auditor invocation: 1, WSLc exit 0.  
Retries: 0.  
Image: python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f (linux/amd64).  
WSLc: 3.0.1.0; --network none; --cpus 1; --memory 512M requested; --pull never; source and audit inputs read-only; --rm. WSL emitted: “kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.” The memory request is not treated as a proven hard limit.

The post-run inventory contained no container running the candidate or auditor. It also showed one newly running container whose inspected source path and command belonged to a separate #5260 checkout/task; it was not ours and was left untouched. Earlier unrelated stopped containers remain unchanged.

Construction-only checks before freeze: AST parsing passed; a host-only preflight candidate/auditor pass produced 6 rows and rejected 4/4 mutations. Those outputs are not pooled with this WSLc formal result.

## Retained files

- candidate.py, audit.py, spec.json — source frozen before run; see source hashes in RUN.json.
- candidate.raw.json — exact candidate stdout.
- candidate.stderr.txt — captured candidate stderr, including the WSL cgroup/swap warning.
- audit.receipt.json — exact independent-auditor stdout.
- audit.stderr.txt — captured auditor stderr, including the WSL cgroup/swap warning.
- SHA256SUMS — source and output hashes.

No GUI, model, GPU, task-effect, runtime-speed, memory-benefit, safety, or production claim is made.