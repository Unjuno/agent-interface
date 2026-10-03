# All-attempt cost coverage repair for #57

An upstream failure, malformed result, or missing model adapter leaves an attempted call without a reported cost. The v3 caller previously compared available costs with completed calls, producing zero or a successful-only subtotal even when another attempted call had unavailable cost. The one-expression repair compares available cost coverage with all attempts. Zero actual attempts still totals zero, and fully covered successful totals remain exact.

This is an ordinary measurement correctness repair, not a provider pricing or efficiency experiment. Costs 0, 5, 7 and 12 are synthetic consistency inputs. Currency, actual provider charges, nonfinite numeric cost validation, latency, token savings, physical effects and end-to-end GUI economics are unqualified.

## Actual verification

- Original nine directed controls: four failures and five passes, preserved in `retained/first-red/`; no failing row was discarded.
- Repaired nine controls plus twelve unchanged existing v3 tests: 21 pass normally and 21 under Python `-O`, in `retained/green-normal/` and `retained/green-optimized/`.
- Saved-data checker: all 27 complete result records checked; exactly four accounting.cost changes, with all other nested result, outcome, ledger, timing and authority fields unchanged. Six copied semantic mutations were refused. See `retained/AUDIT.json` and `retained/audit-run/`.
- Final portable test module, with TRACE_OUTPUT absent: 21 pass normally and 21 under `-O`; full streams, command, working directory, frozen images, PID, start/end UTC and natural exit receipts are in `retained/delivery-normal/` and `retained/delivery-optimized/`.
- A supervisor parse error occurred before the first test launch. Its original script and preparation STOP receipt remain under `retained/`. The corrected supervisor is a separate version.

Host: Windows 11 Home build 26300, CPython 3.12.14, locale CP932 and UTF-8 mode 0. Tests use inert model adapters, deterministic IDs and a virtual clock. No provider, native peer, GUI input, or consumed formal allocation was invoked.

## Integration and preserved evidence

The new module is registered once in the existing `runtime/integration_checks/native.py` protocol catalogue. The existing runner, cwd, PYTHONPATH and other catalogue entries remain unchanged. The two-module local checks establish the caller dependency scope; the whole protocol/harness suite was not rerun and is not claimed passing.

Tested source base: `b4ff90d974c2cd4142eaceee156a74a9aa3109a8`. Delivery base: `d55a1f517a3a889998b82e6d3a359e9f88b82d4e`. The relevant caller, existing tests, native catalogue and six governance document images are identical between these commits; `DELIVERY_AUDIT.json` records that check. No prior PR 7064/7097 refusal/dispatch implementation or review vote is incorporated.

`MANIFEST.json` identifies 53 retained members with original and public byte counts and SHA-256 values. Exact public members are retained here, rather than hashes alone. Files marked private-path-projection replace private host paths with explicit placeholders. Original receipts still identify hashes of private original streams; projected public streams intentionally have distinct hashes. All original bytes stay preserved in the author's private output directory.

Archived scripts and source images end in `.py.txt`; none is executable through Python import or unittest discovery. Their historical RED/STOP results are evidence, not active regressions. The active nine-test module is `research/live_control/test_adaptive_acquisition_cost_coverage.py`. Do not replay historical execution allocations to read or validate saved evidence.

Content committee, immutable proposal, votes and any future current-main application records are kept outside this source tree. Draft publication and local tests are not main integration or completion of #57. Future application must retain genuine nonauthor content approval, current-base/tree coupling and a single history-preserving expected-old main update.
