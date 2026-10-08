# Issue #626 T1 audit compatibility and identity controls

Allocation: `MAP01-THREAT-DEOPT-626-AUDIT-IDENTITY-T1-20261001-01`  
Source main: `7dbe196b8d1fb519139d15240ecb3f377a07b51d`  
Scope: audit-only differential tests over reused synthetic raw evidence. No candidate generation, formal row, container, game, GUI, model, or input.

## H / T / D / C / U

**H.** The new raw-only successor audit preserves the exact frozen #626 auditor's semantic reject behavior for the tested handoff/release/evidence failures, while binding each row to exact case order/ID/pair/arm, runtime bundle hash, fixture ID, and seed. The exact legacy auditor is source-bound to SHA-256 `7ab3d8895c9e8d7c80cf4ff463bac0623fb39247f8aa0d65d34941a1f8c48a40`.

**T.** Reuse T0's exact synthetic raw bytes SHA-256 `121b04c7da14f9e0e0bd1a6a960a2ffbfd22ef879b1d547862191639c5e7a4ce` and fixture bytes SHA-256 `136439478eaa4950668ff28cbe945558229619b5c9a8392de9b27b2ffe04dae8`. Freeze exact legacy source, successor source, fixture/raw, mutation harness and tests. Construction tests precede freeze. Then run one differential harness: pristine baseline; 12 semantic corruption controls through both auditors; 5 row-identity controls through both auditors. The legacy's identity acceptance is a deliberate reproduction of already-known #626 gap, not a scientific result.

**D.** `PASS_AUDITOR_SEMANTIC_COMPATIBILITY_AND_IDENTITY_SCOPED` iff both auditors pass pristine evidence; both reject all 12 semantic controls; successor rejects all 5 identity controls; exact legacy accepts those 5; and every frozen hash matches. Source mismatch or malformed input is STOP; any missed semantic mutation is FAIL. No candidate process is run in this allocation.

**C.** The reused rows are deterministic synthetic contract data; no real MAP01 observation or execution is implied. Controls are hand-authored finite corruptions, not exhaustive fuzzing.

**U.** Does not validate the frozen live runner, prior #626 evidence authenticity, handoff efficacy, formal allocation readiness or live/container gates. It does not change T0's preserved `STOP_LEGACY_SOURCE_HASH_MISMATCH` record or the original #626 0/6 schedule. Independent code review remains required before any use in a formal allocation.
