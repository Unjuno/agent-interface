# A12 one-shot execution record

Allocation: `5309-EVIDENCE-SEMANTICS-HELDOUT-A12-20261007`
Frozen source commit: `85a4eabef3f7eb19403f96065d016dabfe129795`
Frozen base main: `9fb2dd6782d1d1477a00d14be870487fd4c54fa2`

## Preflight

- `FREEZE_SHA256SUMS.txt`: all 8 entries passed immediately before each formal launch.
- `origin/main` remained exactly the frozen SHA.
- All three formal output paths were absent before launch.
- Image/mount smoke: Node v26.10.0, linux/arm64; 192 candidate-input rows read from a read-only bind; writable output bind passed. Smoke artifact: `out/MOUNT_SMOKE.txt`.
- Pre-run construction: `node --check` on all four stage/generator modules passed; `node --test test_protocol.mjs` passed 6/6.

## Formal invocations

| Stage | Container | Invocations | Exit | Result |
|---|---|---:|---:|---|
| Candidate | `ai5309-a12-candidate-20261007` | 1 | 0 | 384 choices |
| Environment | `ai5309-a12-environment-20261007` | 1 | 0 | 384 raw rows |
| Raw-only auditor | `ai5309-a12-auditor-20261007` | 1 | 0 | `PASS_HELDOUT_EFFECT_SEMANTICS_SCOPED` |

No candidate, environment, or auditor stage was retried. All containers used the pinned local image ID and the frozen network-disabled/read-only-root/resource-limited configuration. Candidate mounted only its own source and candidate input; oracle and topology truth were not mounted. Environment and auditor received separate mount sets. `/out` was the only writable mount.

## Retained audit summary

- Cases: 192; arms: 2; raw rows checked: 384.
- Topologies: cycle3 `3:2,2,2`; branch_merge4 `4:1,2,2,3`; asymmetric4 `4:1,1,3,3`; held-out lollipop5 `5:1,2,2,2,3`.
- Correct-prediction stratum: 51 rows per arm; completions GENERIC_IG 22, WITNESS_AWARE 32.
- Misspecified stratum: 45 rows per arm; completions GENERIC_IG 16, WITNESS_AWARE 15. These are counted only when actual receipt evidence supports the realized outcome.
- Prior-witness stratum: 96 rows per arm; completions 96/96; no action taken.
- Held-out, correct, affordable, no-prior: 10 cases; completions 7/10; WITNESS_AWARE advantage +3.
- Non-authoritative candidate completion hints without receipt: 47; unsupported completions: 0; authority grants: 0; audit errors: 0.

## Scope

This is a finite authored method result only. It does not supersede or rewrite A04–A11 and does not establish live GUI, model, physical input, calibrated safety/cost, latency, user, or product behavior. Original raw and audit outputs are retained under `out/`; immutable pre-run hashes remain in `FREEZE_SHA256SUMS.txt`.
