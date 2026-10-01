# Issue #5805 — multi-principal authorization T0

Disposition: `METHOD_PASS_SCOPED` for a synthetic finite policy fixture only. This is not proof of actual consent, identity, ownership, security, application enforcement, or product readiness.

## H / T / D / C / U

- **H:** For a declared co-owned resource, requiring current grants from every required owner blocks cross-owner effects admitted by requester-only authorization; a narrow, current acts-for delegation can restore only its declared operation.
- **T:** Enumerated all 25 ordered pairs from five direct-grant states for owners A and B; evaluated three policies, 75 policy decisions. Separately exercised private-A resource, joint approval, A-only approval, B veto, stale and forged B grants, unknown owner set, exact/wrong-scope/stale delegation, and a bound emergency release receipt. Candidate and separately authored audit use distinct implementations.
- **D:** Scoped pass required the requester-only comparator to admit the planted co-owner violations, both safe policies to deny them absent valid authority, exact delegation to permit its one scoped effect, stale/forged/veto/unknown/out-of-scope cases to fail closed, single-owner work to proceed without an unrelated grant, valid release to remain possible, invalid release binding to fail, and independent audit agreement.
- **C:** The fixture stipulates the owner/resource map and whether a grant/delegation is valid. It does not authenticate a real person, consent, signature, application ACL, revocation source, or effect. The requester-only comparator intentionally ignores B's grant state.
- **U:** Two principals, a small finite evidence alphabet, no concurrency/revocation race, multi-hop delegation, real GUI, OS/app ACL, human study, or legal interpretation. Synthetic authorization behavior is not production enforcement.

## Frozen inputs and execution

- Base `main`: `043ff4bd321ddf89cc3ced0e74f63435bda093f0` (2026-10-01 14:20:54 +09:00); current-main and no-collision check were performed before freezing. GitHub showed Issue #5805 open, with no matching branch, PR, or Issue comments; the additive path did not exist.
- Freeze file: `FREEZE.json`. Frozen candidate SHA-256: `c2701a01e04cdc2a850650089a5a2a4472b60addbe99bb1af85ab901fc9e11e1`; independent audit SHA-256: `410606c460f42d24057dd47b86e987f1d05486bddae9ca18eaf051b308dd3e68`; tests SHA-256: `36234ebf180d8c7e29e683003d75d124c4d3abdb8fbd816731e031114842005e`.
- Construction checks and outputs are separated under `construction_*`; the frozen candidate, raw output, independent audit and test output are retained separately.
- Executed frozen commands once: `python candidate.py`, `python audit.py`, `pytest -q`. Candidate produced 25 state pairs / 75 policy decisions; audit agreed; 5 tests passed.
- Python 3.12.10, standard library only. No model, GUI, human, external service, or task effect.
- Docker Desktop is installed, but during this run its daemon/WSL backend did not answer `docker --context desktop-linux info` within the shell command's 10-second window. No container was started; no image identity exists. This T0 is container-independent. Docker-unavailable is an infrastructure limitation, not a scientific result.

## Results

- Requester-only allowed the shared effect in 4/25 direct-grant pairs where A was valid and B was absent, stale, forged, or had issued a denial.
- All-owner and scoped-delegation policies admitted only the pair where both direct grants were valid in that direct-grant matrix; 0 pair rows had a safe-policy admission without the stipulated valid owner evidence.
- An exact narrow delegation from B allowed the declared annotation while all-owner direct-grant conjunction denied it; wrong-action and stale delegations were denied.
- Owner A's private action proceeded with A's grant and no B grant. Unknown affected-owner set yielded `HOLD_UNKNOWN_OWNER` for every policy.
- A synthetic release receipt bound to actor/resource/action/generation allowed the safety-release lane independently of mutation grants; changing the resource binding denied it. This models relinquishing control only; it is not an emergency-operation policy for arbitrary effects.

Interpretation: the finite policy rules distinguish requester-only, joint-grant, and scoped-delegation behavior as designed. The result demonstrates no facts about actual multi-user consent or enforcement. T1 needs independently authenticated ownership/ACL semantics, a disposable workspace, and separately governed participants; none is allocated by this Issue.
