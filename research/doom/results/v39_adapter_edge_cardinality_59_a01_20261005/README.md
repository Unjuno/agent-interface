# V39 adapter-edge duplicate cardinality — A01

This package tests one data-integrity boundary for Issue #59's per-key timing path. The current projector requires exactly one DOWN and one UP row per identity group. The question is whether identical or contradictory duplicate rows could otherwise be silently treated as one physical edge and expose a timing interval.

## H / T / D / C / U

- **H:** A duplicated DOWN or UP row for the same V39 identity must make the adapter receipt incomplete and must not expose either timing interval. Exact-one cardinality is necessary because replayed duplicate telemetry may be identical and therefore evade field-consistency checks.
- **T:** One frozen retained A01 fixture from #7602 source head `64c48e95425972bc04e61a41d219686c789cb6b6`, plus five cases: identical duplicate DOWN, identical duplicate UP, identical duplicates of both, a conflicting duplicate DOWN, and a conflicting duplicate UP. The candidate extracts only `input_edge_receipts` from the exact frozen controller source. A negative mutation weakens exact-one cardinality to first-row-wins.
- **D:** PASS requires the unique baseline to return one `adapter_edge_brackets_paired` receipt with its exact raw endpoints; each duplicate treatment to return one `adapter_edge_receipt_incomplete` receipt with null endpoints; no authority/application-consumption claim or raw-token leakage; and the weakened guard to pair duplicate cases so the test demonstrates sensitivity.
- **C:** On exact source, all five duplicate treatments fail closed. The weakened first-row-wins guard pairs all five and emits the baseline intervals, including conflicting duplicates. The raw-derived independent audit v2 passes 66 checks and detects an in-memory coherent corruption that falsely pairs a duplicated DOWN.
- **U:** This is one synthetic retained A01 trace and deterministic source projection. It does not establish physical X-server release, application consumption, live threat response, task effect, recovery, or MAP01 completion.

## Frozen identities

- Parent source PR #7602 commit: `64c48e95425972bc04e61a41d219686c789cb6b6`.
- Controller Git blob: `2c42c71985e3a8e16bba11cba3f99181798893d8`; SHA256: `888c3a8f5ea682e0e63d4f63c71a737877829c5a893b427de118d1be958fba8a`.
- Input: `research/doom/map01_v39_perkey_bridge_a01/results/construction-a01/candidate-events.jsonl`; SHA256: `ad0b1c29da4b626e9be27e8716cdabfbb25ac49dcf0abd4bda4bd2f7a9f84e4e`.
- Container image: `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016` (`linux/amd64`, cached local image ID `sha256:414a398990af718f018ff9c23cea0e7489b7986eb54f2b1d7cc874c99ebc7364`).
- Candidate, original auditor, and audit-v2 freezes are retained in `FREEZE.json` and `AUDIT_V2_FREEZE.json`.

## Execution and resource result

The candidate ran once and exited 0 in WSLc. A separate read-only auditor ran once and exited 0; after reviewing the auditor's input-dependence, a separately identified audit-only v2 reconstructed every treatment from the pinned raw fixture and exited 0. No candidate rerun occurred. All containers used one CPU, a 512 MiB memory limit, and `--network none`, mounted source/evidence read-only and output directories separately, used `--pull never`, and auto-removed. WSLc inventory was empty before/after the bounded candidate/audit executions; no GPU, model, game, GUI, or input was used.

The host exposed `cpu.max=100000 100000` and `memory.max=536870912`. WSLc warned that swap limit capabilities were unavailable (“Memory limited without swap”); `memory.swap.max` was `max`, and host `/proc/swaps` showed 16,644,092 KiB configured with 0 KiB used at the candidate observation. No claim is made that swap was constrained.

Candidate outcomes and logs are in `raw/`; auditor outputs and cleanup receipts are in `audit/` and `audit-v2/`. `SHA256SUMS` covers the package files except itself and `verify_package.py`. The verifier independently checks the saved result, pinned raw/source/script hashes, raw-derived audit status, and checksums.

## Regression follow-up

This package tests the exact parent behavior. An additive regression test is stacked on the newer #7602 source branch (`81c77e71111c209b770fb8ce7ef7913134d6d317`), which retains the same controller blob and has separately corrected the interval sweep's admission timestamp. The new test retains the unique baseline and checks identical and conflicting duplicate DOWN/UP rows. `AUDIT_A02_FREEZE.json` pins an AST-isolated WSLc run of that exact test and byte-compilation; it does not change runtime behavior.


A02 isolated regression validation passed: one unittest with five duplicate treatments, exact source/test SHA256 pinned, and both Python files byte-compiled. One harness-only binding error was corrected before the accepted run; the accepted run used one WSLc container and exited 0. Swap limits remained unavailable. Details are recorded in AUDIT_A02_FREEZE.json and raw/a02-regression-container.log.
