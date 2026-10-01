# Exact compiled-runtime staged admission: er197-v1

**PASS: finite exact-runtime development gate. HOLD: production/GUI promotion.**

Issue #197 successor to PR #193. Immutable BASE `4e8e197115969df81a946176e08362c130136603`. All changes are new research files. Shared runtime, historical allocations and live model/GUI work are untouched.

## Materialization blocker resolved

The raw-host download failed DNS, but GitHub MCP `fetch_blob` returned complete UTF-8 source. Saving it and verifying Git blob identity materialized **17,726 byte-exact bytes** of `research/live_control/compiled_gui_interface_v1.py`:

- Git blob: `0c02db714127c8e0f770f9d4ac03699749899d2b`.
- SHA-256: `93e47e1ab5ae3450bb4acf9ec9d21c9abc44ca93ffaee25683b22039d9a722ca`.

The experiment imports and executes that unchanged module. An automatic connector mount or repository clone is not required once returned text can be saved and hash-verified. Earlier SETUP_BLOCKED reports are preserved; #184's different Windows/WSL live environment is not reconstructed here.

## Frozen primary block

736 invocations, one pass: 96 exhaustive certified directional cases + 8 named cases, each with four policies; 64 overlapping-branch cases with five policies. Named cases test unavailable selected guard, same-branch raw movement, changed surface identity and unavailable control in both initial directions.

All policies preserve the same structural surface existence/identity checks. Only control and action-guard validation membership differs. The SQLite owner holds a transaction from `admit` through `execute`. Source-observation sequence and final-state version are distinct retained bindings. Tokens are action-bound, expiring and one-use within the fixture.

|Policy|Cases|Effects committed|Stale effects|False stops|
|---|---:|---:|---:|---:|
|State union|168|9|0|7|
|Selected action guard, no control revalidation|168|44|28|0|
|Same unique selection + selected guard|168|16|0|0|
|Certified selected-when, otherwise full unique fallback|168|16|0|0|
|Unchecked selected-when, overlapping fixture only|64|8|2|0|

**168/168 unique-versus-certified pairs have identical outcomes, reasons and effects.** Both candidates execute all 16 permitted cases, so the result is not blanket rejection. Inactive action guards do not stop the corrected candidate; selected guard, control and association invalidations do.

The certificate uses the actual runtime's Python equality, not type-strict JSON equality. A boolean and an equal integer are not treated as conflicting expected values. No general richer-predicate proof system is claimed.

## One bounded follow-up: the actual callback boundary

Six additional unchanged-runtime invocations, two directions times three deterministic schedules, use a file-backed SQLite WAL database and two real connections:

- stable: 2/2 successful effects;
- writer-first: 2/2 rejected before execute;
- checker-first: 2/2 competing transaction attempts receive SQLITE_BUSY while admission holds the transaction; the effect commits first, and the competing writer then succeeds.

These are deterministic two-connection orderings, not a randomized concurrency-frequency benchmark. This demonstrates expressibility through existing callback APIs, not atomicity of arbitrary GUI clicks.

## Audit and first-outcome retention

Independent `audit.py` does not import the controller. It recomputes expected legality directly from raw pre-effect state and verifies observation digests, receipts, database effects, action/sequence/token binding, transaction closure and the finite candidate result. Four intentionally corrupted records (digest, effect action, receipt count and authority sequence) all fail audit.

All **742 raw records** and their specifications, environments and audits are retained losslessly in `evidence_parts/part-000` through `part-003`. Concatenating these binary parts reconstructs `raw_evidence.tar.xz`, SHA-256:

`bee985d71bf7776ac33c5f9c52be918d58db461fadc1a96a1e987ef77b531cab`

Primary raw JSONL: `054fb83bd20467b06ccf14877bb80adc81d4b02783da440cc42226df46e56174`.
Boundary raw JSONL: `d9719a16e6a1ff7c1d7b1b55b75e1c6160242062b8dc6e79bd559dd83e42ffcc`.

Protocol source hashes were committed before the primary run in `cddbbcee9436561c37d80e546d25133917e8e58b`. The six-run follow-up was frozen locally before execution; one attempted interim Issue comment was blocked and is not claimed as a posted preregistration. No scientific exception or same-ID retry occurred. See `OPERATIONS.md`.

## Reproduction

Tested on Linux 6.18.44, CPython 3.13.5, SQLite 3.46.1; Python standard library only. From this directory, use fresh output names:

```sh
python runner.py --out results/reproduction-01
python audit.py results/reproduction-01
python boundary_check.py --out results/reproduction-boundary-01
```

To inspect the retained first outcome in a clean checkout:

```sh
python unpack_evidence.py
python audit.py results/run-01
```

## H / T / D / C / U

**H:** plan-bound unique-selection plus selected-action guard validation composes with the unchanged runtime; certified equality branches may replace full matching with the selected complete `when`.

**T:** 736 primary runs over 168 distinct finite cases, plus six callback-boundary checks. One invocation per case/arm, not repeated sampling for reliability inference.

**D:** finite exact-runtime gate PASS; both corrected candidates have zero stale effects and zero false stops. General runtime/GUI promotion remains HOLD.

**C:** the fixture supplies known dependencies and a cooperative transaction owner; neither dependency discovery nor noncooperative GUI atomicity is established.

**U:** runtime deadlines use injected virtual nanoseconds. Units match the runtime contract, but values are not measured latency. Release is a simulated adapter contract: no physical input or key state was tested. No model call, token saving, GUI correctness, GPU result or live speed claim. Statistical combined uncertainty and coverage factors are not estimated from this finite enumeration.

## Next boundary

Do not add a new branch mechanism or change shared code on this evidence alone. A real-application successor must establish which component owns validation and effect commit; cooperative SQLite atomicity cannot be assumed for ordinary GUI input.
