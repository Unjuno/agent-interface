# Issue #5550 T0 OrbStack successor 04B

## Disposition

**`PASS_T0_SYNTHETIC_SCOPE_REPRODUCED`** for one bounded, network-disabled
OrbStack replay of the existing fully observed finite DFA. This successor is a
valid in-window reproduction of synthetic evidence only. It does not replace
or rewrite the predecessor allocation's `STOP_ALLOCATION_WINDOW_EXPIRED`
record, and it does not resolve Issue #5550 for real interfaces.

## H / T / D / C / U

- **H:** A correctly frozen, in-window OrbStack replay reproduces the finite-DFA
  candidate output and independent exhaustive audit. **Supported within the
  synthetic scope:** both output hashes exactly equal the prior exploratory
  outputs, under a distinct successor allocation with the declared gates.
- **T:** One candidate container, then one separate raw-only audit container
  after candidate exit 0. See `FREEZE.json` and `RUN_LOG.md`.
- **D:** PASS requires a valid assignment/window, current-main and source
  identities, cached image/platform, empty-container gate, candidate exit 0,
  108 rows and exact predecessor raw SHA, and separate audit exit 0 with
  `errors=[]` and the frozen counters. All observed gates passed.
- **C:** The replay proves reproducibility, not a new plant or generalization.
  The permissiveness result may follow from the hand-authored transition model.
- **U:** Synthetic finite DFA only. No GUI, delayed or partial observation,
  event-classification validity, timing, task success, runtime safety,
  utility/latency, or cross-domain transfer was tested.

## Formal result

- Allocation: `MAXPERM-SUPERVISOR-5550-T0-ORBSTACK-SUCCESSOR-20261001-04B`.
- Window: 2026-10-01 00:50–01:05 UTC, half-open; start gate passed at
  `2026-10-01T00:50:26Z`.
- Frozen main: `7f78c6131a23c0a1a9f6c388ab26a567e5f7dfdf`.
- Engine/context: OrbStack Docker Engine 29.4.0, `linux/aarch64`, context
  `orbstack`.
- Image: `python@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`,
  verified locally as `linux/arm64`.
- Candidate: exit 0; 108 rows; raw SHA-256
  `f17273be18b33083353a883c47c2834a3c33457cb4daada2227aeaf00bd6eb8b`, exactly
  equal to predecessor raw.
- Independent auditor: separate container, exit 0; SHA-256
  `594e785a1a607c7bdab636e3687201fc225d0e0075ca0eec1be6423db60aad2d`, exactly
  equal to predecessor audit; `errors=[]`, `valid_supervisors_exhaustively_enumerated=44`,
  `completed_synthesized=4`, `blocked_synthesized=17`,
  `unsafe_synthesized=0`, `unsafe_greedy=4`.
- Candidate and auditor stderr were empty. Post-run `docker ps --quiet` was
  empty; the lane was released after the two invocations. No retry occurred.
- A separate task reported read-only `image inspect`/`docker ps` at 00:50:21Z;
  our start gate at 00:50:26Z independently observed zero running containers,
  and no conflicting container execution was observed.

## Local validation

- Existing model suite: 7/7 passed.
- Merged prelaunch-guard suite: 14/14 passed.
- The container run exercised CPU-only code with network disabled, read-only
  root/source mounts, all capabilities dropped, no-new-privileges, 1 CPU,
  candidate 512 MiB / audit 256 MiB, and 64 PID limit.

## Artifacts

- `FREEZE.json`: allocation, source/image/main identities and command protocol.
- `RUN_LOG.md`: executed commands, gates, statuses and hashes.
- `raw/formal-01.json`, `raw/audit-01.json`: byte-preserved candidate and
  independent audit stdout; stderr files are retained separately.

This result is strictly a synthetic, fully observed finite-DFA reproducibility
pass. The Issue's partial-observation and real-interface hypotheses remain
open.
