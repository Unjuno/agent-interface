# Issue #5986 — independent container audit of retained T0 raw

## Disposition

**`PASS_AUDIT_REPRODUCED_SCOPED`** — independent audit-only reproduction of the six-row synthetic T0 record.

- Predecessor candidate was not rerun: 0 candidate invocations.
- New auditor: one invocation in OrbStack Docker 29.4.0; exit 0.
- Independent field-by-field reconstruction: 6/6 rows; errors 0.
- New corruption controls rejected: 6/6.
- Raw candidate SHA-256 matched predecessor record: `c3023018f657e33c4d6a9bf70a956bfa030b04fdde32671a096e1d0a02a51a2f`.
- Pre-run local construction tests: 9/9 passed. Formal mutation controls ran once inside the auditor container.

## What the audit confirms

The original raw's six classifications, clock-derived fields, synthetic action-effect diagnostics, and costs are exactly reconstructed by a separate implementation that imports neither predecessor `candidate.py` nor predecessor `audit.py`. It also rejects promotion of the synthetic delta to verified value, an invented post-deadline window, delivery claims for an undelivered cue, stale-generation promotion, a fabricated action/effect, and erasure of the mandatory-safety refusal. The mandatory cue remained delivered; the fixture's withholding request was refused.

This makes the retained finite taxonomy/accounting result independently reproducible in a pinned container. It is not a new candidate allocation and does not establish causal value of feedback timing.

## H / T / D / C / U

- **H:** A separately implemented raw-only auditor in an isolated, pinned container reproduces every retained row and rejects all predeclared corruption controls.
- **T:** Candidate 0 times; new independent auditor 1 time; retries 0. Source, fixture, candidate raw, predecessor audit and their hashes are frozen in `FREEZE.json`. OrbStack Docker command and restrictions are in `PROTOCOL.md`.
- **D:** `PASS_AUDIT_REPRODUCED_SCOPED`; six rows exact, six mutations rejected, exit 0. Audit JSON SHA-256: `0d07fb11f1bf509296db04764ce2311d0ce4590457b42c8ac4c529b78f1899f7`.
- **C:** Docker Engine 29.4.0, Python 3.12 slim ARM64 pinned by digest; network disabled, read-only root and source mount, separate output mount, 0.5 CPU, 256 MiB, 32 PIDs, all capabilities dropped, no-new-privileges. Nine local tests passed before the formal audit.
- **U:** Authored synthetic fixture only. No new candidate behavior, real model/GUI/user/app, real safety, task effect, feedback benefit, latency, human tempo or population claim. This does not test #6129's pending/censored route-learning hypothesis.

## Reproduction

See `PROTOCOL.md` for the exact single container command. The container used `--rm`. The task workspace itself is not a Git checkout, so repository-wide local CI and a Git diff check were not available here; the package construction suite and isolated formal Docker audit were executed directly. Do not report this scoped validation as repository-wide CI.
