# Issue #8327 A02 — independent audit of retained #8319 A01 factorial raw

## Disposition

**PASS_AUDIT_ONLY.** The independent raw-only auditor reconstructed all 400 rows, found no record mismatches, and rejected all six frozen mutations. Its single formal CLI invocation exited 0. The exact A01 input raw was verified against its preregistered SHA-256 and left byte-identical. No candidate was rerun; retries were zero.

This pass validates the internal consistency of the retained finite synthetic record under the written A01 protocol. It does not rewrite, erase, or retroactively change A01's original `HOLD_AUDITOR_GATE_FAILURE` outcome or PR #8321's historical audit output. It supplies a distinct successor audit artifact for independent integration review.

## Frozen inputs and execution

- Issue: [#8327](https://github.com/Unjuno/agent-interface/issues/8327), audit-only successor to #8319 A01.
- Base: `main@798ac5ad709168ff1d27b115f10f4f96b126bb71`, checked against GitHub and `git ls-remote` before freeze and again before the formal audit.
- Allocation: `8072-FACTORIAL-AUDIT-8319-A02-20261007`.
- A01 input: copied from branch `research/8072-factorial-8319-20261007`, commit `5e23f00fb98e24c078077ba4869a292d4120f7ab`; the copied bytes have SHA-256 `ecffd8121a289d3533c94373c8f7aba50d9c349ffd5db534e46db16522897e9d`.
- Freeze SHA-256: `ea6b0021e6cadf1b75674845ae81251a89982d2e113e0bd149c0a20f70b40b91`.
- Frozen auditor SHA-256: `56c819bec9d1c63252f22bfd1d6b063d5683ef48ac7389d2e942b3d774b1b0b3`; tests: `17cfa554d2c77b6e4ddd07858a13823944209f7a65affc7135e2baf1a2825315`.
- Construction: four tests passed; tests cover the exact decision-gate success case, wrong row count, reconstruction error, and the A01 inverted-mutation-count regression. `py_compile` and `git diff --check` passed before freeze.
- Formal command, once only: `python3 auditor.py inputs/a01_candidate.json results/audit.json` — exit 0. No candidate invocation, no retries.
- Formal audit output SHA-256: `a1fa82a600f901303c00c44e826342f03d79be4f22ffad8b1a15792baced191f`.
- Runtime: macOS arm64, CPython 3.14.5, standard library only. This audit did not require container isolation and makes no isolation claim.

## Independent gate result

The auditor imports neither A01 candidate nor A01 auditor code. It reconstructs the factorial cells from the written protocol, compares every retained row, and independently applies six mutations: feedback-mode substitution, updater identity substitution, early fresh-cohort exposure, omitted safety disclosure, altered fresh marginal, and forged feedback response.

| Gate | Result |
|---|---:|
| Rows observed / reconstructed | 400 / 400 |
| Reconstruction mismatches | 0 |
| Mutation controls / rejected | 6 / 6 |
| Undetected mutations | 0 |
| Formal CLI exit | 0 |

The A01 defect was a CLI decision inversion: its helper reported an empty list when all mutations were rejected, while its entrypoint expected a list of length six. This successor's tested gate passes only for 400 rows, zero reconstruction errors, and zero undetected mutation names; a list containing six undetected controls fails.

## Local CI and validation

- Successor construction suite: 4/4 PASS.
- Analysis index checker: PASS, 769 retained result/failure directories indexed; its unit suite: 22/22 PASS.
- Analysis sparse-checkout dependency suite: 3/3 PASS.
- Research workspace index unit suite: 22/22 PASS; committed-tree index check: PASS, 160 top-level directories reachable.
- `git diff --check`: PASS; the modified Analysis Index workflow parsed successfully as YAML.
- The CI-pinned Python 3.12 runtime also passed the successor suite 4/4, analysis-index tests 22/22, and sparse-checkout dependency tests 3/3.

An initial ad-hoc combined unittest command used a dotted import for the workspace suite and failed with `ModuleNotFoundError`; the repository's documented `unittest discover -s research` route was then used and passed 22/22. This was a test-command routing error, not a source or formal-audit failure.

## C / U — scope

This is a verifier-integrity result over a deterministic, authored synthetic record. It does not establish that the authored update rules represent researchers, validate behavior outside this finite design, or adjudicate a general feedback-superiority claim. No candidate, model, human, GUI, privacy, product, or real-world safety claim is made. #8072 A01/A02 and #8319 A01 artifacts remain unchanged.
