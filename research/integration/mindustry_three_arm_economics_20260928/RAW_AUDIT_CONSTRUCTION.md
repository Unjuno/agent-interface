# Independent raw-allocation auditor — local construction rung

Date: 2026-09-29 JST. Parent hypothesis and economic decision thresholds remain frozen in #5130/#1679.

## H / T / D / C / U

- **H:** An auditor independent of the live runner can reconstruct the exact #1679 evaluator trace from event-level preflight, image, model-call, input-admission, feedback, release, submission, private-score, timing, and B1-repair records. It rejects summary-only records and contradictory/missing evidence. A valid reconstruction preserves the frozen economics decision; valid-but-uneconomic evidence remains `REJECT`, not an audit failure.
- **T:** Use a deterministic synthetic raw record with three arms × six tasks, frozen routes/layouts/call counts, model-call usage, two local image events per task, two admitted palette/world inputs per task, release receipts, independent placement-score rows, and the required persistent-B1 stale-reference refusal plus fresh repair call. Run the 12-case host test suite and retain the raw synthetic bytes and JSON audit output. Image hashes, model calls, commit, and container digest in this fixture are explicit placeholders; they are not real frozen identities. No Docker, model, Mindustry process, socket, or formal allocation.
- **D:** PASS construction only if the synthetic events reconstruct to the expected normalized trace and evaluator result; missing releases, old-target admissions, wrong effect evidence, source/image mismatch, schedule drift, injected aggregate fields, or mismatched independent source freeze must hold/reject. The audit must label an unpinned fixture `PASS_CONSTRUCTION_ONLY`; only an exact match to a separately supplied freeze may return `PASS_RAW_RECONSTRUCTION`.
- **C:** The frozen arm/task schedule, usage and correct effect are held fixed for the positive trace. Negative controls each change one raw event, identity, or evidence condition. One separate positive-but-high-token trace tests the distinction between a valid raw audit and an economic `REJECT`.
- **U:** This verifies parser/reconstruction logic against synthetic records only. It does not prove that a future runner emits truthful/raw-complete logs, that source hashes match actual files, that the image/asset/container pins are correct, or that any Mindustry task occurred. The external freeze is supplied separately by the audit operator; live runner integration and raw-source byte rehashing remain gates.

## Current local result

The first auditor test run failed 2/9: one assertion expected different refusal wording, and one fixture serialized a JSON object with sorted arm keys while the parser incorrectly treated object-key order as meaningful. The parser now validates the exact arm set and emits evaluator arms in frozen order; the test expectation now matches the fail-closed error. These were retained construction defects, not benchmark outcomes.

Rerun command (repository root):

```powershell
python -m unittest discover -s research/integration/mindustry_three_arm_economics_20260928 -p test_raw_allocation_audit.py -v
python -m unittest discover -s research/integration/mindustry_three_arm_economics_20260928 -p 'test_*.py'
python research/live_control/probe_integrated_efficiency_protocol_v1.py
python research/live_control/probe_receipt_target_admission_v1.py
node --check research/integration/mindustry_three_arm_economics_20260928/mindustry_mod/main.js
git diff --check
```

The unit suite passes **12/12** and reconstructs a synthetic `RETAIN` at task-2 break-even; 8 corruption controls are rejected/held, and the valid-but-high-token case remains an evaluator `REJECT`. The full package passes **72/72**. The unpinned raw artifact is intentionally marked `PASS_CONSTRUCTION_ONLY`, with `source_identity_verified=false`; its raw SHA-256 and full JSON output are in [`construction/raw_audit_v1_20260929_01/`](construction/raw_audit_v1_20260929_01/). The standalone CLI requires an operator-supplied, independently retained freeze for formal `PASS_RAW_RECONSTRUCTION`.

Current source baseline is main `708dec9bcd2bfb3ef597acf7bc1c8a02bcb96b01`; the three intervening upstream commits changed no #1679/#55 dependency blobs. The full package suite, inherited evaluator probe, and Issue #55 no-GUI receipt probe are run locally only. No GitHub Actions result is used.

Docker remains unavailable to this lane by policy, not engine capability: #5130 explicitly forbids all container start/build/pull/inspect/alter until a named coordinator grants the exact lane and sibling-container release is reconciled. Latest #5085 comments still report no authorization. Do not interpret this host construction as a formal audit or result.

## Lifecycle-complete v2 successor

V1 omitted raw reset snapshots and A3→B1 geometry receipts. The additive v2
auditor and its separate synthetic result are documented in
[`SOURCE_IDENTITY_AUDIT.md`](SOURCE_IDENTITY_AUDIT.md); v1 raw bytes are
unchanged. The v2 fixture independently validates 18 reset witnesses and three
geometry transitions, still at `PASS_CONSTRUCTION_ONLY` only. Full integration
suite is now 82/82 locally. Current source baseline is `bbe4bd3b3fadea09679c8956cdd2d35988acd2d3`.

## Adversarial JSON boundary successor (2026-09-29)

Local malformed-input probing found that a 401-digit JSON integer in the
private reset tick projection escaped `audit()` as `OverflowError`: Python's
`math.isfinite(int)` attempts a float conversion. This was an auditor crash,
not a benchmark outcome. The v2 checker now treats Python integers as exact
finite values and applies `math.isfinite` only to floats, allowing the invalid
monotonic reset pair to return `HOLD_RAW_RECONSTRUCTION`. A regression control
retains the 10**400 mutation. Final v2 tests are 10/10 and the full package is
82/82; inherited and receipt no-GUI probes pass. This synthetic adversarial
boundary check is host-local and does not change the immutable v2 raw artifact
or elevate its `PASS_CONSTRUCTION_ONLY` scope.
