# Issue #6483 T0 — bind critical speech spans to authenticated principals

Status: local construction; formal candidate/auditor have not run.

## H / T / D / C / U

- **H:** A segment/principal gate can preserve clean authenticated requests while
  returning SOURCE_UNKNOWN, YIELD, or non-actionable for mixed, replayed,
  unauthenticated, quoted, or non-jointly-authorized spans. Transcript-order and
  cluster-only baselines can misbind an effect-critical span.
- **T0:** Nine finite no-audio/no-model scenarios × four fixed attribution
  policies (transcript-order, cluster-only, authenticated push-to-talk,
  segment/principal gate) = 36 assigned policy rows. Scenarios cover a clean
  request, overlapping cross-speaker negation, wrong-principal command,
  quoted command, stale replay, cluster switch, high-confidence cluster
  without authentication, missing joint authorization, and explicit joint
  authorization. A separate oracle supplies source truth. Four source-binding
  corruptions swap owner, splice a negation, refresh a stale generation, or turn
  cluster confidence into an identity grant; a fifth corrupts the denominator.
- **D:** `METHOD_PASS_SCOPED` only if the segment gate has zero wrong-principal
  actionable proposals, rejects/holds stale and unauthenticated sources,
  avoids cross-principal composition, treats quotes as non-actionable, preserves
  clean single-speaker and explicitly authorized joint requests, and the auditor
  rejects all five planted corruptions. This validates representation only.
- **C:** A trusted, genuinely single-speaker push-to-talk channel may be simpler
  and sufficient. Synthetic authenticated-session fields assume what a future
  trusted channel would have to provide; diarization scores are not identity.
- **U:** No acoustic recognition, liveness/spoof detection, biometric identity,
  user consent, model proposal behavior, live GUI action, or real principal
  authentication is tested. No transfer or safety claim follows.

## Frozen boundary

All data are synthetic structured traces. There is no audio file, model call,
human participant, biometric processing, external service, credential, or
effectful action. The T0 gate is upstream of speech-act interpretation,
content-preservation, and normal action admission; it does not replace them.
Construction checks are distinct from the single formal candidate and auditor
invocations. Recheck Issue/branch/PR ownership and current main before the
preregistered formal start. Any failed gate is a preserved STOP, not a retry.

## Roles

- `scenarios.json`: assigned synthetic segments, session evidence, generations,
  overlaps, cluster guesses, and policy-baseline inputs.
- `oracle.json`: independent segment-principal truth and expected gate outcomes;
  scenario input is bound by canonical-JSON SHA-256 so CRLF/LF checkout rules
  do not alter the semantic input identity. `SHA256SUMS` binds exact LF Git-tree
  bytes for the complete package.
- `candidate.py`: evaluates four fixed attribution policies without oracle
  access.
- `auditor.py`: reconstructs outputs from raw scenarios and oracle without
  importing candidate code, then applies the four source-binding and one
  denominator mutation controls.
- `construction_tests.py`: local deterministic construction/mutation suite.

Eligible execution uses Microsoft WSL Containers (`wslc.exe`), a locally pinned
Python image with pull disabled, network none, one CPU and no GPU. Any WSLc
swap/cgroup warning is retained; a requested memory limit is not assumed to be
enforced.
