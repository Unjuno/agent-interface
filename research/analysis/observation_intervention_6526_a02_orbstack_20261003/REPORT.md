# Issue #6526 A02 — OrbStack formal result

Allocation `OBSERVATION-INTERVENTION-6526-A02-ORBSTACK-20261003-01` completed its one frozen 180-trial candidate and one independent raw-only audit. A01 remains its own immutable `STOP_AUDIT_ERRORS`; no rows were pooled or reused.

## Result

`H_FAIL_SCOPED` (method-valid, scoped negative). The auditor reported zero integrity errors and reconstructed all 180 expected randomized starts, action schedules, action callbacks, and independent deadline snapshots.

| Schedule / arm | Effects missing at deadline | Miss rate |
|---|---:|---:|
| SENSITIVE / MINIMAL | 0/30 | 0.000 |
| SENSITIVE / SCREENSHOT | 0/30 | 0.000 |
| SENSITIVE / SHAM | 0/30 | 0.000 |
| STABLE / MINIMAL | 0/30 | 0.000 |
| STABLE / SCREENSHOT | 0/30 | 0.000 |
| STABLE / SHAM | 0/30 | 0.000 |

Screenshot-minus-MINIMAL and screenshot-minus-SHAM sensitive miss-rate differences were both 0.000. Both preregistered one-sided exact paired McNemar p-values were 1.0. Stable controls passed (30/30 each). One action callback arrived after its 100 ms sensitive deadline; the independently sampled effect was absent at the deadline but present later. It remained an outcome as preregistered, not a method error. The zero-miss pattern does not support the preregistered ≥0.20 intervention effect.

This is not evidence of equivalence, no observer overhead, or safety: the fixture, host, 30 matched blocks, single action timing, and chosen deadlines bound the claim. It does not test browsers, accessibility-tree reads, real applications, human/model action, production prevalence, or other platforms.

## Execution and custody

- Candidate: one container, exit 0, receipt count 180, restart count 0.
- Independent auditor: one separate container, exit 0; raw-only reconstruction, no candidate execution or candidate-code import.
- Same immutable image: `sha256:a14e964ad615fa8315eec5f1e2539eb781f10647872c42e0cbe5b1400c15cb45`, `linux/arm64`; Docker Engine 29.1.3 in the private OrbStack VM.
- Both containers: `--init --network=none --cpus=1 --memory=512m --pull=never`; auditor inspection confirmed CPU quota 1,000,000,000 nanocpus, memory 536,870,912 bytes, and network `none`. Candidate input mount was read-only; output was separate writable storage.
- Frozen input SHA-256: `2f80ca7855e5bc5158bf4ea0ce0e20e4f7d84d9c3dcd18fe4b073fcf7b29f5ce`. The preregistered source hashes and construction audit/smoke receipts are in `FREEZE.json`.
- Full candidate raw output is retained under `results/formal-a02/raw/`; independent output is `results/formal-a02/audit.json`. `results/formal-a02/SHA256SUMS.txt` covers every retained raw/output file.
- Construction was separate: six-case construction audit, Xvfb/Tk/xwd smoke, 13 local tests. None of those were formal observations.

## H/T/D/C/U disposition

- **H:** Not supported under this exact synthetic condition; frozen positive threshold missed. Classified `H_FAIL_SCOPED`, not STOP and not equivalence.
- **T:** Completed the single 180-trial randomized allocation and one raw-only audit.
- **D:** All allocation, timing-origin, callback, deadline-oracle, and capture integrity gates passed; all six effect rates were 0/30 misses; exact paired p=1.0 for both sensitive comparisons.
- **C:** Event-loop, thread, X11 capture, CPU, filesystem, and fixture-specific behavior remain plausible limits; sham and matched block design do not identify beyond this host/fixture.
- **U:** One synthetic Tk app, one ARM64 OrbStack VM/host, 30 blocks, one action delay/deadline design. No production or safety inference.

## Successor boundary

Do not repeat the same 180-trial allocation or relax its threshold after seeing outcomes. A successor is justified only by a materially different, prospectively specified condition (for example, a different independently motivated deadline/action regime) and must preserve both A01 STOP and A02 `H_FAIL_SCOPED` unchanged.
