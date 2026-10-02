# Preserved preformal capsule — Issue #4295

This is an additive preservation copy of the frozen preformal capsule from
`research/specialist_regeneration_4295-20260923`. The source archive and every
extracted member are retained byte-for-byte; `source/SHA256SUMS.txt` validates
the extracted members. This path records a construction-only revalidation and
does not publish a formal result.

## H / T / D / C / U

- **H:** For a tiny deterministic four-entry specialist with complete local
  support, deterministic regeneration plus full-support attestation may
  preserve the versioned lifecycle's predicate/UNKNOWN/fail-closed semantics
  while reducing GENERAL calls after support or producer-version changes.
- **T:** The frozen standard-library experiment compares `ALWAYS_GENERAL`,
  `VERSIONED_SHADOW_SWITCH`, and `REGENERATE_AND_ATTEST` over eight fixed
  schedules and two repetitions, with 128 request rows. It has no GUI, model,
  provider, network, or OS-input authority.
- **D:** The preregistered scientific gate requires all 128 rows, oracle
  agreement, zero stale specialist use/UNKNOWN coercions/authority, safe
  fail-closed controls, at least eight fewer GENERAL calls for regeneration
  over the 48 version-change/recovery rows, and a clean independent raw audit
  with at least 10 coherent corruption controls rejected. The frozen source
  declares formal invocations before freeze = 0; no formal invocation is
  included in this preservation or revalidation.
- **C:** Construction uses a complete fixture support table and deterministic
  regeneration. Real learned specialists may have expensive or nondeterministic
  training, calibration needs, or incomplete support.
- **U:** No learned-model quality, natural drift, task effect, token/latency,
  GUI/OS authority, cross-application, or production claim follows.

## Construction revalidation (2026-10-01)

- Frozen `SOURCE.tar.xz.b64` decoded to XZ SHA-256
  `4bd7965d9119a222ca37bdc1cabdb0c2bd33c61f104d65f1a21571125a36ec9`.
- All ten extracted source members passed `source/SHA256SUMS.txt`.
- Container: `python:3.13.5-slim@sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419`;
  Docker engine 29.4.0; network disabled, root filesystem read-only, source
  mounted read-only.
- Command: `python -B -m unittest -v test_contract`.
- Outcome: **5/5 construction contract tests passed** (0.000 s); the
  construction-shape test returned the frozen 40 construction rows.
- Scope: this validates only the committed construction/test contract under
  the pinned Python container. It does not execute any formal schedule, create
  formal rows, run the formal auditor/controls on formal data, or resolve the
  regeneration-versus-lifecycle hypothesis. Scientific status remains
  **NOT RUN / UNRESOLVED**; no PASS is claimed for Issue #4295.
