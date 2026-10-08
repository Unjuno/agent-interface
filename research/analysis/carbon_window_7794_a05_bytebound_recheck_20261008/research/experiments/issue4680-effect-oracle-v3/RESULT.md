# Issue #4680 — explicit postcondition audit v3

## Decision

**`PASS_POSTCONDITION_ORACLE_SCOPED`** for this offline deterministic replay audit. The full #4680 adapted-skill composition remains **HOLD**: the #4205 adaptation prerequisite and #4670 measured fast semantic backend are still unmet. This is not an application-effect, model, speed, or #4680 completion claim.

The independently authored oracle recomputed all ten retained proposals against a separate bounded settings transition model. All ten proposal objects exactly match their frozen case expectations; all ten persistent postconditions match; the linked `SET_FIELD(digest_frequency=weekly)` → `CLICK(save_settings)` is consistent; all 9 unit tests pass; and all 4 mutated evidence controls are rejected with typed audit errors. For `NO_ACTION`, the oracle derives an already-satisfied requested value from the case's intent and persisted state without using the expected-effect label in that derivation. The v2 oracle failure remains preserved separately and unchanged.

## H / T / D / C / U

- **H:** The case `effect` field represents a persistent requested postcondition, not always a state delta. An independent oracle can derive the satisfied-state postcondition for `NO_ACTION` and independently simulate the deterministic proposals.
- **T:** One local, network-disabled Docker run; stdlib-only tests + independent replay audit of the single retained predecessor result; four adversarial evidence mutations. No predecessor proposer/auditor/runner was rerun.
- **D:** PASS for this narrow replay contract: proposals 10/10; recomputed postconditions 10/10; linked save path valid; tests 9/9; corrupt controls rejected 4/4; all predecessor source, case, package, result and freeze identities matched.
- **C:** Same fixed ten settings fixtures and deterministic SkillPackage proposals from `issue4680-skillpackage-construction-20260927-01`. Oracle source shares no imports with that proposal runtime/auditor. Previous effect-oracle allocation v2 returned `FAIL_ORACLE_IMPLEMENTATION` because it confused no-op with empty postcondition; that first result and its raw output are retained in `../issue4680-effect-oracle-v2/`.
- **U:** No real application/UI transition, Astra demonstration, Needle adaptation, learned semantic backend, performance, amortization, generalization, action authority, or user-task correctness evidence. The oracle is a small manually specified model of this fixture contract.

## Frozen provenance and execution

- Allocation: `issue4680-explicit-postconditions-20260927-01`.
- Predecessor freeze SHA-256: `14332efe92338a8252b3ad31f80ef6dab0c26a178bcf936366d16d1c7e67c3ef`.
- Predecessor raw `result.json` SHA-256: `aad85a7121c28fe82f28fc6d28cf114c02383fd44a3ade3240e9a7fa2e5876ca`.
- This allocation's freeze SHA-256: `01e5e371778efd266a39549b2e37b433bba0f1e236934df42a1a23c1e98c3832`.
- Local image: `python:3.11-slim`, ID `sha256:da047cb8f9d1d98e5c070f5300ba9f7274e33b8fc0e5be5ed88740aed1b95ba9`, linux/amd64.
- Limits: no network, 1 CPU, 128 MiB, 16 PIDs, read-only root/input, 16 MiB noexec/nosuid tmpfs, no-new-privileges, all capabilities dropped.
- Runner exit status: 0. Source identity check: all 5 frozen v3 files exact. Predecessor identity checks all true; original nine predecessor source hashes matched.
- `outputs/formal01/audit.json`: `PASS_POSTCONDITION_ORACLE_SCOPED`, 10 rows, no errors. `outputs/formal01/controls.json`: 4/4 rejected.

## Raw output SHA-256

| File | SHA-256 |
|---|---|
| `outputs/execution.json` | `6051151ea79c16f84ad95b42fad130479da86120795bf363c43f723d959b39ad` |
| `outputs/tests.stderr` | `0ab9bec4a942130ef59016decfeda3add52d4503c511892ad304888427cc838a` |
| `outputs/formal01/audit.json` | `e870a7589c19b986ef3533ee0634b991599d7a7cfc0cfc60f212ceb9e8c3eed2` |
| `outputs/formal01/controls.json` | `6226e9f39f2db0797059d886f92e62e4d2b31ef8005bb76a881fabf4e87be60d` |
| `outputs/tests.stdout`, `outputs/audit.stdout`, `outputs/audit.stderr` | empty file SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

## Next research boundary

Do not promote this fixture simulator to an application claim. A meaningful next step is a separate, preregistered construction using an independently implemented application-like state machine and its own externally checkable postcondition oracle, before any learned/adaptation composition. Keep the original #4205/#4670 prerequisites and no-retry limits in force.

