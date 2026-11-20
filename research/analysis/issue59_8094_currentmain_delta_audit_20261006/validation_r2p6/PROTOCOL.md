# #8243 verifier correction: engineering plan and frozen gates

Purpose: correct this conversation's unsupported 8/8 execution claim and test an
actual source-bound verifier. This is engineering under #59/#8243, not a new
scientific hypothesis, GUI allocation, #8094 code review or product result.

H: the original verifier can accept invalid or falsely source-bound tables;
explicit validation against a complete local Git object database can reject them
without changing the positive three-addition/eight-edit contract, in normal and
optimized CPython. A saved hash/summary alone cannot prove the source relation.
T: first retain the exact three original blobs and excluded discovery. Write and
run failing regression tests before implementing v2. Freeze a 20-case matrix:
three positive encodings/orderings and 17 directed negative payloads, two
verifiers, normal and -O: 80 bounded subprocesses. Each has its exact input,
argv, stdout, stderr and return code. Both verifiers receive identical copies.
The local Git fixture has real commits/trees/blobs at the selected 11 path names,
but synthetic file contents, not executable V39 code. A complete Git bundle is
retained. No GUI/model or old scientific allocation is invoked.
D: original failure is retained. The new verifier must accept all six positive
mode-cases, reject all 34 negative mode-cases, require actual local source
objects, and report no application/input/task authority. Missing receipts or
source changes are HOLD/STOP. A separate auditor validates row membership,
inputs and outputs against the fixed independent decision list. Counts are
engineering test cases, not rates or confidence intervals.
C: an attacker who controls verifier and repository defeats this trust model.
Git object integrity is not authentication; fixture completeness does not prove
all #8094 dependencies. This v2 checks only the explicitly selected eleven
paths, not the entire PR or semantic runtime compatibility.
U: provided Linux x86_64/CPython3.13.5 container, no WSLc/Docker/OrbStack image
attestation. No shared workstation/GPU/game lane. One serial workload, no timing
benchmark, no calibrated uncertainty or coverage factor. Git binary and all
sources are SHA-256 pinned. No installation or experimental network; an earlier
unauthenticated source-download attempt failed DNS, and MCP supplied exact bytes.

## Implementation steps
1. Exact Git-blob restoration of old verifier/result/controls; preserve them.
2. Test fixture and regressions -> original RED -> explicit source-aware v2 -> GREEN.
3. Public complete source/readback and local hash freeze before the new 80-case run.
4. One matrix invocation; separate raw audit, no mutation/retry of recorded rows.
5. Additive qualification and evidence PR; do not manufacture review approval.

## Variables and units
| Name | Meaning | SI unit | Definition and range | Type |
|---|---|---|---|---|
| path | 対象のリポジトリ相対パス | not applicable | Fixed 11 distinct ordinary file paths | string |
| base/main/candidate | 比較するcommit | not applicable | 40 lowercase hex object identifiers | strings |
| expected_accept | 独立に指定した受理期待値 | dimensionless | three positives, 17 negatives | boolean |
| returncode | 実process終了値 | dimensionless | observed integer, no inferred zero | integer |
| timeout | 各processの上限 | s | 5 seconds for Git calls and verifier calls | scalar |

Unit check: compared identifiers have no physical units. Test denominators count
subprocess outcomes, not seconds, applications or independent users. No latency
or physical-key measurement is derived from these records.

## Premeasurement startup correction
The first full construction command returned four subprocess timeout errors;
all failures and exact old sources are retained. A single excluded no-op startup
check took 3.034 s with ordinary system-site initialization and 0.016 s with -S.
This is a setup diagnostic, not a performance result or a proven explanation for
every timeout. The declared subject commands now use -S -I -B with optional -O,
so no system site/.pth package initialization is required. Verifier logic, input
cases, 5 s child limit and acceptance gates are unchanged.
