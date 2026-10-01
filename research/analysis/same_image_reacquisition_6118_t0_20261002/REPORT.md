# Issue #6118 T0 — same-image reinterpretation versus fresh acquisition

## Result

**`PASS_METHOD_SCOPED`** for the preregistered synthetic accounting/decision taxonomy only. The one-shot candidate exited 0; the separate raw-only auditor exited 0 with seven cases and zero errors. Candidate invocation=1, auditor invocation=1, retries=0. The audit does not establish a beneficial review policy or visual correction effect.

## H / T / D / C / U

- **H:** A finite, no-model accounting method can distinguish computation over immutable image bytes from later acquisition, retain denominator/trigger/cost accounting, and prevent correlated or stale outputs from authorizing an action.
- **T:** One frozen seven-case table; one network-disabled pinned ARM64 candidate container; one separate auditor container only after candidate exit 0. Candidate had access only to `candidate.py` and `fixture.json`, never `truth.json`. Auditor read the exact candidate raw, the visible fixture and the auditor-only truth sidecar.
- **D:** `PASS_METHOD_SCOPED`; 7/7 unique case IDs, independent truth controls satisfied, image/epoch/cost ledgers matched, stale cases required fresh acquisition or YIELD, review agreement did not grant authority, all rows had `action_authorized=false`, and errors were empty. Six mutation controls were rejected by the pre-run construction tests (9/9 tests passed).
- **C:** All labels, pixels-as-symbolic-tokens, decisions, and cost units were authored. A YIELD or an independent typed cue may dominate rereading. The T0 uses no image model or actual capture pipeline.
- **U:** No visual-recognition accuracy, correction rate, calibration, actual token/time benefit, optimal policy, real app state/focus, hidden-state persistence, effect verification, safety, or product claim.

## Case-level observations

| Case | Retained T0 observation | Method boundary exercised |
| --- | --- | --- |
| adequate-inferential-error | Initial `BLACK` disagreed with oracle `READY`; blind and grounded rereads both returned `READY`. | Same-image correction is recomputation, not independent confirmation; downstream gates remain required. |
| aliased-pixels | Blind and grounded rereads both returned wrong `BLACK`; independent typed cue was `READY`. | Correlated agreement does not resolve inadequate pixels; seek independent cue or YIELD. |
| changed-world | Capture epoch 30, current epoch 31; old `READY`, truth `SAVED`. | Old-frame reread cannot establish current state; require fresh acquisition or YIELD. |
| same-bytes-new-epoch | Recapture digest matched while epoch advanced 40→41; oracle state remained `UNKNOWN`. | Later capture can support a time-indexed persistence observation only; not hidden-state or effect proof. |
| high-confidence-trigger-miss | Confidence 0.99, no trigger, wrong first answer, no review outputs. | Trigger miss remains in the denominator; the candidate YIELDED and authorized no action. |
| answer-anchoring | Blind reread matched `READY`; answer-grounded critique changed to wrong `BLACK`. | Preserve disagreement; do not majority-vote or promote critique. |
| no-error-overhead | First answer was already correct; triggered blind/critique outputs were unchanged. | Ledger retained 2+3=5 review cost units (6 including first read), zero correction; units are synthetic. |

## Formal execution provenance

- Issue: https://github.com/Unjuno/agent-interface/issues/6118
- Allocation: `same-image-reacquisition-6118-t0-20261002-01`
- Frozen main: `3adec9cdc2cff5ef68f19acd55c5823fcaad26df`
- Corrected freeze/source commit: `bb34f78ecf172a8c0fea8f7b40f928b1242a90ad`; pre-run digest correction is preserved in `FREEZE_CORRECTION_01.md`. The initial freeze commit remains in history; no formal invocation occurred before correction.
- Runtime: OrbStack-managed Docker Engine 29.4.0; image `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`; inspected image platform `linux/arm64` and image ID equal to the pinned digest.
- Isolation: network none; read-only root; 32 MiB noexec/nosuid tmpfs; all capabilities dropped; no-new-privileges; 32 PIDs; 256 MiB; 0.5 CPU. Source and fixture mounts read-only. Candidate received no truth mount. Auditor received read-only raw/truth; only the dedicated audit-output directory was writable.
- Candidate: one invocation, exit 0, stdout empty; wrote seven JSONL rows. Auditor: one separate invocation, exit 0; disposition `PASS_METHOD_SCOPED`, errors `[]`.
- Execution window as observed from UTC clock reads: `2026-10-01T15:39:01Z`–`2026-10-01T15:42:12Z` (2026-10-02 JST).
- Raw SHA-256: `2c1552dcc25653b41b26223e1d65b03c39132dd25c87dcb346a6727a2b3657f6`.
- Audit SHA-256: `97caebc061842092b21195715d4df6f9862d80549f1e0094afc97cdf4e89bb7e`.
- The pre-existing `unjuno-native-ci-6092` container was observed at 0.00% CPU / about 112 KiB and left untouched. No other container was stopped, inspected internally, or modified.
- No Obstac-specific CLI or MCP endpoint was exposed in this environment. The formal container runtime is accurately reported as OrbStack Docker; it is not claimed as an Obstac-managed run.

Exact argv, exit codes, preflight receipts, hashes, and outputs are in `RUN.json` and `SHA256SUMS.txt`. `FREEZE.json` binds source SHA-256 identities and the decision gate. Reproduce only as a new allocation; do not rerun allocation 01.

## Local CI

The relevant local CI commands, outputs, and workflow-vs-host boundaries are itemized in [`LOCAL_CI.md`](LOCAL_CI.md). All applicable local gates passed, including the workflow's network-disabled Docker replay gate; GitHub-hosted Actions remain a separate integration signal.
