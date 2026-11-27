# MAP01 process identity implementation plan

> Execute inline using superpowers:executing-plans, with existing read-only reviewer.

**Goal:** Carry opt-in process-incarnation evidence from current MAP01 capture
through immutable lease admission to V12 press/held-input checks without moving
identity I/O onto its cleanup connection.

**Architecture:** Reuse the existing read-only TargetQueryWorker and trusted-local
XRes/Linux process-start reader. Give capture and owner separate readers. Keep the
strict existing pointer-binding shape; transport identity in a separate field.
Freeze sequence/XID/digest at Executor admission before accepted publication.
Selected V12 checks it before new input and during held input. Preserve original
deadline, telemetry, one input writer and sticky reader retirement.

**Spec:** [Observed current-owner gap](../../../research/live_control/v12_generation_boundary_20261016/RESULT.md).
Base `067bc1ad7ef2fb226256089c17766a4048428322`. Python/X11; Fake X tests only.
User's FINAL v5 delegates implementation/local validation/integration; no new
review quorum or live-resource grant is introduced by this plan.

## Design constraints

- Explicit `--target-process-identity` through V39 controller and V15 measurement
  session. Existing defaults remain unchanged; V12 default session cannot select it.
- Capture brackets the actual image with XID/digest samples and refuses mismatch
  before typed/full delivery. Only confirmed full observation becomes lease source.
- Optional Executor `bind_lease_source` hook runs under admission lock before any
  accepted receipt, freezes current sequence/focus/surface/geometry/digest, and
  cannot renew the lease. Absence of this hook preserves other backends.
- V12 opt-in requires a positive source XID and lowercase 64-hex digest. No fallback
  to numeric focus on missing/changed/unavailable proof. Release bypasses identity.
- Separate read-only worker waits check retained cancel/stop/original expiry.
  Translate remaining perf-counter budget once to worker monotonic wait, then
  recheck original lease after return. Reader errors/late replies retire permanently.
- Held-input checks preserve source identity and source deadline. Generation failure
  uses a retained interruption reason understood by cooperative lease wake logic.
- Native focus, send/sync/readback and capture can still block. No physical release
  bound, window incarnation, atomic server acceptance, task effect or efficiency claim.

## Tasks and evidence

- [x] Add failing owner tests: fresh/stale/unbound, prefix release, held revocation,
  stalled identity with cancellation/expiry, late reply retirement, release bypass.
- [x] Add shared reader + opt-in V12 check; retain V4/V3 telemetry and interruption wake.
- [x] Add selected backend capture→source hook and Executor admission integration.
  Test mismatch during capture, missing source, source mutation after acceptance,
  and actual selected owner input/refusal/cleanup.
- [x] Add explicit standard caller/session selection and selected source manifest.
  Test flags, invalid nonmeasurement selection and default compatibility.
- [x] Run focused and affected normal/-O suites. Preserve first failures and scoped
  limits, obtain available read-only review, repair findings without rerunning raw.
- [ ] Publish/integrate exact source under actual protection, update #59/#17 as
  appropriate, retain original generation-gap packet and clean only own refs.
