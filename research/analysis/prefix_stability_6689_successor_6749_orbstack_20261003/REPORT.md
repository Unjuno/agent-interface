# Issue #6749 — corrected prefix-stability successor T0

## Result

**`PASS_METHOD_SCOPED`** — one frozen candidate and one independent auditor ran once each in separate OrbStack containers; retries were zero. This is a finite authored method result only.

- 32 frozen worlds, 2,112 legal interleavings, and 4,064 distinct evidence prefixes were reconstructed independently.
- Candidate raw SHA-256: `f5d665cb5a767abdc501d9fdfbafa4d96866671847a27e7a26dd54985e3fb1b0`.
- Independent audit SHA-256: `b14333316ce5d5186448891027d604e27222b5b969b6408e092361a842abe677`.
- Auditor errors: none. All five frozen mutations were rejected: dropping a pending mandatory obligation, mixing derived metrics into disposition counts, forging completion, stale→current relabel, and timeout→complete relabel.
- A current-generation mandatory FAIL can be stable before all checks/sources finish; outstanding mandatory and frontier obligations remain explicitly listed. PASS requires both mandatory PASS results, CURRENT generation, and explicit optional COMPLETE.
- Disposition counts are `CLOSED_FRONTIER_REQUIRED=30`, `PROVISIONAL=446`, `STABLE_FAIL=1662`, `STABLE_PASS=60`, `STABLE_UNKNOWN=1866`. Derived metrics are separate: `EARLY_FAIL=690`, `EARLY_UNKNOWN=786`.
- Authority grants and consumer-side effects: zero.

This directly exercises the two distinct predecessor defects recorded without alteration in #6689's PR #6704 and PR #6706. It does not reclassify either predecessor. The construction-stage first fixture was insufficient because CLEAR could not be followed by CONFLICT; that pre-formal finding and amendment to add the continuation are retained in `PREREGISTRATION.md` and the #6749 issue comment.

## H / T / D / C / U

- **H:** A corrected prefix-stability classifier and independent oracle preserve unfinished obligations under decisive negative results and keep disposition counts disjoint from derived metrics.
- **T:** A finite asynchronous evidence model with two mandatory sources, one immutable generation status, and four optional-source paths; candidate and raw-only oracle in separate network-disabled, resource-limited OrbStack containers.
- **D:** PASS required exact per-prefix reconstruction, retained obligations, no premature PASS, disjoint aggregate fields, rejection of all five mutations, and zero authority/effects. All passed.
- **C:** Wait-for-all or #6509's claim-scoped partial verdict may be simpler; the model is authored and finite.
- **U:** No runtime, GUI, real verifier, freshness, action safety, latency, user, or product behavior was tested.

## Execution and reproduction

The pinned local image was Python 3.12 slim Bookworm, linux/arm64, image digest `sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`, under OrbStack Docker Engine 29.4.0. Candidate and auditor each exited 0 in separate network-none containers with read-only root filesystems, 1 CPU, 256 MiB configured memory, 64 PIDs, all capabilities dropped, no-new-privileges, and UID 1000. The auditor received the candidate raw read-only. Configured cgroup limits are not asserted to have been independently enforced.

Full preregistration and amendment: `PREREGISTRATION.md`; exact commands: `RUNBOOK.md`; frozen source identities: `FREEZE.json`; invocation IDs, exit codes and hashes: `RUN_RECORD.json`; raw/audit: `results/formal_01/`. No candidate or auditor retry occurred.
