# Strict locations for native and public receipt references

Parent integration question: #57. Worker `01a0ff52-5884-7172-a388-d9ac576e13dd`, policy FINAL-v5. Branch `research/local-control-01a0ff52-20261003`. Base/source intake `11f1bae6f8dbfd280b6ccbd0def0bc23fa5da68d`.

## Engineering result and limits

**RETAIN_SCOPED_POINTER_REPAIR; main integration pending independent agreement.** A native v1 receipt and a public v2 event receipt previously accepted noncanonical array pointers (`-1`, `00`, `+0`, whitespace, Unicode digits). Python list/index coercion selected locations not identified by the declared JSON pointer. Missing, out-of-range and scalar traversal leaked KeyError, IndexError or TypeError instead of the ValueError receipt boundary. Invalid escape sequences could select literal dictionary keys. Existing native v2 already had a stricter resolver.

The runtime change factors that existing resolver into `_json_pointer`, keeps native scope checks in `_native_pointer`, and reuses the strict resolver in native v1 and public event expansion. Canonical array tokens, escaped dictionary keys, numeric-looking dictionary keys and `/report` root references retain their meaning. Compactor round trips and caller inputs remain exact. No raw evidence is changed by this projection operation.

These are ordinary input-free engineering/finite-oracle checks, not a formal allocation, benchmark or live experiment. No backend, OS input, model, GPU, container or shared runtime was invoked. No claim of a live exploit, task improvement, semantic correctness, token/latency benefit, broad GUI reliability or physical release follows. Direct native reference helpers had no product call sites at the pinned base outside their module; the public event expansion API is also repaired, without claiming all public clients necessarily exercise it. General malformed top-level containers and arbitrary custom Python objects remain outside this change.

## H / T / D / C / U

- **H:** reusing the existing strict decoder rejects malformed pointer locations while retaining lossless valid projections.
- **T:** retain test-first failures; execute finite baseline/fixed matrices; independently reconstruct expected outputs or typed refusal from frozen JSON inputs; run corruption controls, relevant CLI checks and committed distribution checks.
- **D:** every final candidate row equals the independent oracle, invalid paths raise ValueError, all valid controls remain exact, and caller objects are unchanged. Original failures remain retained.
- **C:** dictionaries permit keys such as `-1` or `00`; only array tokens require canonical ASCII nonnegative integer spelling. Markers and declared scopes still govern whether a location is a reference.
- **U:** the finite deck is deliberately bounded. Real delivery, backend/clock/GUI/model behavior and general arbitrary Python object handling are unmeasured. Hosted CI and foreign platforms are not inferred from local checks.

## Retained sequence

1. `baseline.py.txt` is the exact pinned original source (SHA-256 `27543a4faff97a4917b63a8ee3e9c6965474087da160f0e8cdfd2203e6d72e01`). Native tests first failed with 9 assertion failures and 4 wrong-boundary exception errors; `execution/test-first.log` is retained.
2. The first native-only fix is retained as `native-fixed-v1.py.txt`. Prepared `PLAN.json`, 194 frozen cases, both raw records and independent audits remain unchanged: baseline **48 violations**, fixed **0**, **50 valid controls**. `native-test-v1.py.txt` was reconstructed by removing the subsequently added event regressions; its exact bytes were checked against the original PLAN's pre-matrix test SHA-256. It is not represented as an original filesystem copy.
3. Inspection exposed the same cause in public event expansion. Four added test methods first failed with 9 assertion failures and 2 wrong-boundary exception errors; `event_boundary_v2/test-first.log` is retained. A separate prepared plan and 98-case deck were used: baseline **48 violations**, final fix **0**, **26 valid controls**. `event_boundary_v2/source.py.txt` is the exact final runtime source.
4. The final factored runtime also passed the original 194-case native deck: zero violations, 50 valid controls (`event_boundary_v2/native-final-raw.json` and `native-final-audit.log`). This is a compatibility verification, not independent new science or pooled evidence.
5. Two separate raw-only oracle programs import no runtime, runner or backend. Native and event auditors each reject their nine declared corruption controls; normal and optimized Python controls pass. The native original oracle has bounded equality semantics; the event oracle compares JSON serialization to preserve scalar types.

## Local validation

The final relevant CLI/API suite invoked 146 tests, with **140 passing and 6 expected skips**. All 39 focused optimized-mode regressions passed; 10 focused pointer test methods passed. Normal/optimized event audit controls and compilation passed. All nine distribution tests passed; an isolated Python process imported only the archive built from committed source `c5dc56f2e` and passed all ten pointer regressions. `event_boundary_v2/archive-manifest.json` binds its exact source file hashes and archive digest. Distribution/archive commands have observed aggregate shell exit 0 and retained logs, without separate per-command wall-clock/exit receipts. Commands, observed process exit codes and wall-clock start/end records for the final stages are retained in `event_boundary_v2/commands.json` and `validation.json`. They are execution provenance, not latency measurements. The initial native-only stages have tool-observed completion and aggregate shell success; they have no separately captured per-stage process-exit receipts. No status is backfilled.

Initial sparse-checkout probes lacked selector modules, and a broader pre-fix presentation check lacked optional `mcp`. Those were local environment limitations, not pointer failures. The owned sparse checkout was expanded, and `mcp==1.30.0` was installed only in a dedicated validation venv. Final local Python is 3.12.13 on macOS arm64; optional MCP transitive packages are recorded separately. Six skipped checks do not prove their platform/backend conditions. The system Xcode Git license was not accepted; explicit available Git 2.54.0 was used. No global setup/configuration change was made.

## Reproduce the finite engineering comparison

Use Python 3.12 or later from the repository root. New output files must not exist.

```sh
P=research/integration/native_reference_pointer_57_20261003_01a0ff52
python "$P/matrix.py" "$P/native-fixed-v1.py.txt" "$P/fixtures.json" /tmp/native-reference-own-output.json
python "$P/audit.py" /tmp/native-reference-own-output.json "$P/fixtures.json" "$P/native-fixed-v1.py.txt" --require-clean
python "$P/event_boundary_v2/matrix.py" "$P/event_boundary_v2/source.py.txt" "$P/event_boundary_v2/fixtures.json" /tmp/event-reference-own-output.json
python "$P/event_boundary_v2/audit_event.py" /tmp/event-reference-own-output.json "$P/event_boundary_v2/fixtures.json" "$P/event_boundary_v2/source.py.txt" --require-clean
python -m unittest runtime.cli_v1.test_native_reference_pointer -v
python -m unittest discover -s "$P" -p 'test_*.py' -v
python -m unittest discover -s "$P/event_boundary_v2" -p 'test_*.py' -v
```

Full byte inventory is `MANIFEST.json`; source/log snapshots are inert `.py.txt` or explicit retained data. Current-main combination, two distinct digest-bound nonauthor approvals, applicable GitHub conditions and conditional main application remain separate delivery gates. Common fleet deadline/model-effort settings were not available from this execution; none is invented or changed. No input, shared lease or application lock is held.
