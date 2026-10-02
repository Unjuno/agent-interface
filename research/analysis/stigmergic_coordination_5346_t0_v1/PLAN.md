# Issue #5346 — scoped stigmergic coordination T0

Status: source and decision rule frozen; formal container allocation has not run.

## H / T / D / C / U

**H.** In a two-worker contention schedule, a valid visible local marker can
reduce collision retries versus no coordination, while using fewer coordination
events than central explicit claims. Markers remain advisory: every side effect
still requires the ordinary authoritative lease gate. This does not predict
behavior of strategic agents or real UI workers.

**T.** One deterministic finite-state first unit: nine declared schedules ×
three policies (`NO_COORDINATION`, `CENTRAL_CLAIMS`, `LOCAL_MARKERS`) = 27 cells.
Schedules cover visible contention, delayed observation, marker loss, forged
marker, stale generation, duplicate delivery, owner crash/lease expiry, external
generation mutation, and no contention. Two workers and two tasks/targets (A/B)
are fixed. The candidate, runner, raw-only auditor, command file and thresholds
are SHA-pinned in `FREEZE.json`. Construction tests do not consume the formal
allocation. Exact read-only/network-disabled commands are in
`CONTAINER_COMMANDS.md`.

The formal run is exactly one network-disabled `linux/arm64` OrbStack container
invocation using the locally cached, platform-verified Python image digest in `FREEZE.json`, with
read-only source and a separate output mount. If and only if the runner exits 0,
run one separate network-disabled raw-only auditor container. No GPU, model,
GUI, input, external effects, retries, or raw overwrite. A fresh exact shared
CPU slot and successful image/platform check are required first. The proposed
09:20–09:25 UTC request expired without authorization; therefore no container
has been invoked and no formal result exists.

**D (frozen decision).** `PASS_FIRST_UNIT_SCOPED` only if all 27 cells complete
both tasks exactly once, every admission cites `authoritative_lease`, the raw
auditor passes, and in `visible_contention` local markers reduce collision
retries from 1 (no coordination) to 0 while using 2 coordination events versus
4 central-claim messages. Delayed, lost, stale, and forged hints must fall back
to the authoritative collision/re-observation path; duplicate delivery must
deduplicate; owner crash must recover only after lease expiry; external mutation
must cause stale-generation refusal and fresh observation. Any missing case,
false effect, marker-derived authority, or audit mismatch is `FAIL_T0`. A
container/image/resource preflight failure is `STOP_INFRA`, not a scientific
failure. No-contention overhead is reported, not hidden by the primary case.

**C.** This is a hand-specified two-worker discrete-event model with logical
ticks, not measured wall-clock or production coordination. It is not exhaustive
over 2–8 workers, strategic behavior, clock skew, real trace visibility, real
leases, or UI/backend side effects. Central claims and local marker events use
different accounting units (request/grant messages versus publish/observe
events); report them separately and do not call them equivalent network costs.

**U.** No result can establish production safety, human/agent behavior, reduced
real latency/cost, or suitability for implementation. A positive first unit
justifies a larger exhaustive schedule enumeration; a negative/STOP result is
retained without retuning this allocation.

## Execution record

- Current main at freeze: `afb7a91983a782f06ae12ebfbe8f802376f69d22`.
- Host construction suite: 15/15 passed; py_compile passed.
- Current OrbStack inventory at 2026-09-30 09:17 UTC: daemon `linux/aarch64`,
  no running containers, host architecture `arm64`. This is not a slot grant.
- Selected cached image `python:3.12-alpine` inspect confirms image ID/digest
  `sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b`,
  OS `linux`, architecture `arm64`, repo digest identical. No pull was needed.
- Additive branch `research/stigmergic-coordination-5346-t0-20260930` was created
  from `main`; immediate compare was identical at `afb7a919...`.
- Coordination request #5085 comment `5908272385` proposed 09:20–09:25 UTC and
  expired without grant. No formal runner/auditor container invocation occurred.
- Refreshed request #5085 comment `5908359395` proposes 10:51–11:01 UTC; still
  no lease. Image/platform identity is now verified using the cached alpine
  image above. No formal runner/auditor container invocation occurred.
- The active task workspace is not a Git checkout. Focused unittest (15/15) and
  `py_compile` are local; repository-wide local CI and `git diff --check` were
  not run in this workspace. Evidence will be committed through the prepared
  GitHub branch after the one-shot result is available.
