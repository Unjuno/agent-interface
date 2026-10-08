# #6613 service-debt/deadline A01 result

**Disposition: `FAIL_HYPOTHESIS` (synthetic finite-trace scope).** The candidate and independent raw-only auditor each ran once in separate OrbStack Docker containers. Both exited 0; retries 0. The auditor independently replayed all 288 policy × seed × stratum rows with `PASS_RAW_REPLAY`, `errors=[]`. The service-debt policy failed the preregistered wait-improvement gate; do not tune or rerun this allocation.

## H / T / D / C / U

- **H:** Service-debt/rotating-tie scheduling was expected to reduce mean per-trace worst eligible wait versus FIFO and shortest-service-first under recurring asymmetric arrivals, without loss of the on-time floor, mandatory work, or eligibility controls.
- **T:** 32 fixed holdout seeds (10000–10031) × 3 strata × 3 policies = 288 rows; each trace contains six A/B requests per principal and, in the rights-control stratum, one mandatory interrupt. Integer ticks, single nonpreemptive server. Candidate and independent auditor were run once each in distinct pinned-image containers.
- **D:** Failed: in the asymmetric stratum, mean per-trace maximum wait was debt **33.28125**, FIFO **31.875**, shortest **32.28125** ticks. Thus debt is worse than both baselines and `no_asymmetric_wait_gain` is the sole decision reason. The on-time optional-completion floor passed in all three strata: asymmetric 117 vs weaker baseline 109; burst/recovery 129 vs 121; rights/interrupt 103 vs 102. No accounting/safety audit errors were found.
- **C:** Service-duration debt alone can trade off against waiting time for queued work; short-service-first also completed more on-time optional work here. The result is specific to this fixed generator, scheduler implementation and finite seed range.
- **U:** No human principals, live shared GUI, real authority, real service-time calibration, production fairness/safety, task benefit, or product claim. No recommendation to deploy a scheduling policy follows.

## Reproduction and environment

Base main/source `aec152dca5d9a28d916761421a74c703600df683`; freeze commit `fc6f171ad33e6a39338bdb6ab7b778720ada3696`. Image `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, linux/arm64; OrbStack Docker Engine 29.4.0, kernel `7.0.14-orbstack-00380-ga7e0a2dc9535`. Network disabled, pull never, read-only source/root, UID/GID 65534, 1 CPU, configured 256 MiB and 64 PID cap, all capabilities dropped, no-new-privileges. Both containers exited 0 and `OOMKilled=false`; in-container `memory.max=268435456`, `pids.max=64`. The cgroup memory value is recorded as observed, not a swap-limit or general isolation guarantee. Existing container `unjuno-native-ci-6092` was not touched.

Candidate container ID `269a3b3a11ba4e25636c0318c810d732accdf58c0875dd4dadfc4a3ad5c66353`; auditor container ID `23271059c8e7f83bde34fedb799d22257c1af093652e55cfeeb5d21d910c066b`. Candidate raw: 557,828 bytes, SHA-256 `774e950e7ff434f3c768337bfc763d33a41af2da6b6ac1a74f73269c6328b25c`. Audit JSON: 866 bytes, SHA-256 `408c14501efb9ba30710d1bdca8b48f4812e03bbbdd8b1ff51df3f1bda467398`.

Post-run focused tests: 4/4 pass; Python bytecode compilation and `git diff --check` pass. The four tests include separate construction-seed replay, seed-disjointness, ineligible-dispatch mutation refusal, and mandatory-interrupt omission refusal. These are construction/audit checks, not additional formal runs. Complete commands, output hashes and runtime receipts are in adjacent `FREEZE.json` and `SHA256SUMS`.
