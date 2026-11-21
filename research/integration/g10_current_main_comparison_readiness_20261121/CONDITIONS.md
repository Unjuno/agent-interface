# G10 to current comparison-contract readiness audit

## Freeze

- Audit ID: `G10-COMPARISON-READINESS-20261121-R01`.
- Current main: `ce6449f38a56e1731f01d1024837fb34c9c759a3`.
- Historical source allocation: `CALC-COMPILED-OCR-3311-4D74-CONSTRUCTION-G10-20261004`.
- Historical source commit: `9823419dc71eb6f7fd745bfe8249cf7f7584a3a9`.
- Input packet: `research/integration/calc_current_shared_3311_4d74_20261004/calc-compiled-ocrlive-4d74/`.
- Comparison contract: `research/integration/standard_mcp_task_ledger_57_v1/recorded_comparison_adapter_v1.py` at SHA-256 `9680761627e72a1986304eb8985b89280fe74d74f93aef9a2375ec02065aeac1`.
- Scope: read-only custody/hash verification and schema-admission probe. Do not launch Calc, OCR, Docker, WSLc, a model, or any input process. Do not edit or regenerate historical G10 artifacts.

## H / T / D / C / U

- **H:** G10's retained live effect is reusable as a narrow positive-control result, but its record cannot be admitted as a matched efficiency arm under the current comparison contract because complete provider/caller events and lifecycle accounting are absent.
- **T:** Verify all source hashes declared by G10's `PLAN.json` against its retained `sources/` snapshot; verify every retained run file and write a deterministic manifest; call the current `build_measured_run` with the unmodified G10 raw object and verify explicit rejection; enumerate available and missing contract fields from the pinned adapter constants and retained raw records.
- **D:** PASS the audit only if source hashes and raw-file custody verify with zero mismatches, the adapter rejects the unmodified G10 record for the expected receipt-contract reason, and the report classifies it as ineligible for matched efficiency while retaining its narrow effect-control use. Any mismatch or unexpected adapter acceptance is FAIL and must remain visible.
- **C:** G10 used seven retained local OCR subprocess attempts and two guarded native programs, so some execution detail is present. A custom translator might produce a partial record, but it cannot reconstruct unknown primary provider usage, absent matched arms, or omitted all-attempt model events. Do not reinterpret UNKNOWN as zero.
- **U:** This is an offline schema/custody audit. It does not re-run the live task, verify the historical auditor independently, prove provider-side completeness, or establish any speed, cost, reliability, MAP01, or Research Preview outcome.

## Frozen expected observation

G10's archived `raw.json` is expected to have an empty top-level `events` list and no reconciled recorder receipt fields (`complete`, `raw_refs`, `unresolved_attempt_ids`, `unresolved_tool_call_ids`). Its original `AUDIT.json` reports `primary_usage: UNKNOWN`. The current adapter requires these caller receipt fields and a validated run envelope. This expectation is fixed before executing the audit.

## Commands

Run the audit twice against the same immutable checkout, once with normal Python and once with `python -O`; write outputs only into this new packet. The two JSON results must be byte-identical. No experimental allocation or GUI action is consumed by this audit.
