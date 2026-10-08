# #6695 A01 result: exact staging frontier, no uniform benefit

`PASS_METHOD_SCOPED`: one candidate and one independent auditor, both exit 0; zero retries; all 6,912 rows reconstructed with zero errors. This certifies the frozen finite discriminator. It is not a policy-efficacy PASS or a recommendation to stage every action. Prior #6707/#6709 results remain unchanged.

| Policy (2,304 authored schedules each) | Correct on-time irreversible commits | Wrong on-time commits | Deadline refusals |
|---|---:|---:|---:|
| IMMEDIATE (diagnostic) | 864 | 864 | 576 |
| WAIT_THEN_PREPARE (simple matched comparator) | 972 | 324 | 1008 |
| STAGE_THEN_CORRECT | 894 | 558 | 852 |

The matched comparator receives exactly the same signal at the same time as staging. It performs initial preparation after the signal; staging prepares A beforehand and may need an additional edit to B. For informative B with a correction route, staged readiness minus waiting readiness is exactly `e-min(p,s)`, as derived with SI units and types in [PROTOCOL.md](PROTOCOL.md). The frozen grid includes 10 staged-only correct/on-time schedules and 22 waiting-only schedules in this slice. It includes 36 exact-deadline staged admissions and 36 one-ms-short refusals. Correction time can erase or reverse overlap benefit. Across the whole grid, waiting produced more correct commits and fewer wrong commits. Aggregate authored counts do not estimate natural rates or establish a generally optimal policy.

The absent-correction-route control is asymmetric by the actual modeled mechanism: staging cannot change an already prepared target, while waiting may select the right target before preparation. UNKNOWN signals cannot change either target. Deadline refusals produce no irreversible effect; modeled benign work may finish after the deadline. A 1ms commit completes on equality. IMMEDIATE ignores added information and is diagnostic; it is not the strongest efficacy comparator.

## Evidence and independent validation

- [Prospective freeze](FREEZE.json), [protocol and H/T/D/C/U](PROTOCOL.md), [construction history](CONSTRUCTION_HISTORY.md). Source commit is recorded outside the frozen source in [EXECUTION.json](EXECUTION.json).
- [Candidate raw JSONL](formal_01/candidate/RAW.jsonl), [independent audit](formal_01/audit/AUDIT.json), all stdout/stderr/exit receipts; [manifest](SHA256SUMS). Candidate simulator and auditor algebraic oracle import neither each other nor predecessor code.
- Host construction 6/6 and private-Docker construction 6/6; seven actual corruption cases rejected (readiness, target, scalar type, omitted event, late commit timestamp, missing row, duplicate row). These tests use private mini-fixtures, not a second execution of the formal grid.
- Candidate mounted only candidate.py and public fixtures.json, never truth.json. Auditor received scorer truth separately. Guest-to-host raw and audit readback hashes matched.
- Raw SHA-256: `c31bc33ee1718823a93c9eb30c2eafca235dc1f40688af363fad4746f8ec6305`; audit SHA-256: `1293c25830a476ba8e34032e1fa058294645ef2c991c93fd1674d039e4bbe88e`.

## Runtime and limitations

macOS Apple Silicon host, owned normal-mode OrbStack Ubuntu 24.04 guest/private Docker 29.1.3, Linux 7.0.5-orbstack, linux/arm64 Python 3.12.15. Digest-pinned Python base, pull-never/offline computation, uid65534, read-only root/sources, capabilities dropped, no-new-privileges, 64-PID cap, one CPU and 256MiB requested. Construction readbacks were memory.max=268435456 and cpu.max=`100000 100000`; these are configuration observations, not host-wide enforcement or pressure-test proof. Outer execution wall times are in EXECUTION.json and include launch/readback overhead; they are not application latency or matched performance measurements. Runtime network was used only during setup/image acquisition. Original host-path receipts are retained privately; published commands replace only the source prefix with `$SOURCE`.

The earlier --isolated-machine Docker launch failed before process start with a BPF/cgroup error and is preserved as construction infrastructure failure. It consumed no formal candidate/auditor invocation. The successful VM uses standard host integration, not OrbStack --isolated mode; formal container mounts/no-network are the admitted boundary. No shared Docker change, privileged container, GUI, input injection, GPU, model, user data, real application effect, token/human-tempo or natural failure-rate evidence.

Disposition: retain this exact conditional frontier; do not promote a universal staging optimization. Any live follow-up needs independently measured preparation/edit/reversibility bounds and effects, matched observations/deadlines, and separate authorization/resource allocation. Main publication requires FINAL-v5 nonauthor content approval and current-base combination verification; a PR is evidence handoff, not scientific completion.
