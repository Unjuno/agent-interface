# Issue #5739 audit-v2 pre-execution freeze (read-only; no candidate rerun)

## H / T / D / C / U

- **H:** A newly versioned, independent raw-only auditor can reconstruct the exact already-retained Issue #5739 candidate artifact, its 32 sealed assignments, three claim labels and seven corruption controls without invoking or importing the candidate.
- **T:** Read exactly `candidate_raw.json` SHA-256 `64f387c791f6bd87efdb05f07c9418a7631012f5203cb14bfacef3f8432ac7ea`; reconstruct expected assignments and labels directly from frozen `world.json`; verify source identities; reject missing/duplicate/repeated-variant/altered-family/forged-safety/unsupported-global-best/unadjusted-promotion mutations. The auditor reads `runner.py` bytes for identity only and does not execute it. No model, application, GUI, network, Docker or experiment input is involved.
- **D:** `PASS_CLAIM_BOUNDARY_SCOPED` only if audit-v2 exits 0, reconstructs all 32 assignments and expected labels, reports zero global-best claims, and rejects 7/7 mutations. Any mismatch is `FAIL_AUDIT_V2_RECONSTRUCTION`; infrastructure or auditor execution errors remain typed STOP. Audit-v1's `STOP_AUDITOR_REPORT_SERIALIZATION` remains unchanged.
- **C:** This repairs/evaluates the retained raw evidence boundary only. Exact agreement on authored finite fixtures is not external method validation.
- **U:** No new candidate run, empirical claim, performance estimate, Docker evidence, task effect, safety claim, runtime savings or product conclusion.

## Execution contract

- Same research question / Issue #5739; audit allocation: `issue-5739-t0-a01-audit-v2`.
- Frozen branch: `research/5722-claim-boundary-successor-20261001`; base main remains `24f6b7d5f9395105807f981d48db212e6692a6f4`.
- Candidate raw, world, runner, audit-v1 STOP and audit-v1 source are immutable inputs on this branch. No candidate source, input or raw file is changed.
- One command, at most once: `python -B audit_v2.py`.
- Host: Windows x86_64, CPython 3.12.10; CPU only.
- `audit_v2_result.json` was absent before the audit. No retry or code change after the audit command.
- This is the explicitly versioned read-only audit permitted by `docs/ISSUE_FAILURE_CLASSIFICATION.md`; it does not erase or upgrade the failed audit-v1 invocation.

## Frozen SHA-256

- Candidate raw: `64f387c791f6bd87efdb05f07c9418a7631012f5203cb14bfacef3f8432ac7ea`
- Candidate world: `5329331f1948d7db6fb58244473dddbc1391c841c709b6de9b8ede31a7316441`
- Candidate runner: `f9e0d06048538c8e942ed450938b8550348aafc0a093be2c6f17c8fc9b7448bc`
- Failed audit-v1 source: `469c0555d875f998a85f545419fb3a92f344287f1515a014880ab50e9290e3b5`
- Audit-v2 source: `c0f1ac21a1c081deea1b8e6bf0714e15cc40a6a9a887e6bdcde024abcbaffc76`
