# Issue #7650 T0 A02 read-only row-binding audit successor

## Result

`PASS_ROW_BINDING_AUDIT_SCOPED`. This read-only successor consumed the exact A01 raw bytes without rerunning A01 candidate or auditor. The frozen auditor verified the input SHA-256, reconstructed 960/960 unique IDs, matched every row's family/task-language/embedded-language/class/variant fields to the same UID, checked all 12 metadata cells (80 rows each), preserved every semantic judgment as `UNKNOWN_NOT_ADJUDICATED`, and rejected all seven preregistered controls. Of particular relevance, swapping task-language fields between rows while preserving aggregate marginal counts was rejected by per-row UID binding.

The result qualifies—but does not erase—the A01 audit defect documented in [`A01 POST_REVIEW_CORRECTION.md`](../crosslingual_visual_injection_7650_t0_a01_20261008/POST_REVIEW_CORRECTION.md). A01 raw bytes and initial stdout/audit output remain unchanged. A02 establishes only internal metadata-ledger consistency for that exact synthetic artifact.

## H / T / D / C / U

- **H:** A raw-hash-bound audit with per-row UID binding rejects aggregate-preserving metadata corruption while accepting the exact frozen A01 artifact.
- **T:** The A02 auditor ran once after Issue preregistration; the test suite exercised seven mutation/hash controls. A01 candidate and auditor were not rerun.
- **D:** Predecessor raw hash, source/test/protocol hashes and one-shot output hashes are in [`FREEZE.json`](FREEZE.json) and [`INVOCATIONS.md`](INVOCATIONS.md).
- **C:** The frozen raw passed; all 960 IDs and 12 balanced cells were reconstructed; all 7/7 controls were rejected. `PASS_ROW_BINDING_AUDIT_SCOPED` applies only to this ledger.
- **U:** There are no English/Turkish linguistic stimuli, translations, screenshots, or pixels. Semantic equivalence, naturalness, visual legibility, model susceptibility, language-congruence effect and external validity remain unknown. Issue #7650 full T0 remains HOLD.

## Execution

Host Python 3.14.5 on macOS 27.0.1 arm64, stdlib, read-only audit only. No container, model, inference, GUI, participant, network, tool proposal or external effect. Four construction tests passed before freeze; `py_compile` and `git diff --check` passed. Exact first formal output is retained; no retry.
