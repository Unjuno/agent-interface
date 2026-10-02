# Exploratory result — Issue #5805 finite joint-authority contract

## Disposition

`PASS_METHOD_SCOPED` on a fixture-authored authorization-admission model only. This is exploratory local evidence, **not** a formally allocated repository experiment. The Idea issue allocated no experiment branch; the present change only preserves the already-run evidence in an additive review branch and does not alter that allocation status. Candidate/auditor were run once each, locally and separately; no retry or rerun for publication.

## H / T / D / C / U

- **H:** Requester-only admission exposes missing co-owner authority, while all-owner conjunction blocks the frozen bad-authority cases and exact scoped delegation preserves one narrow valid operation.
- **T:** 17 fixed traces × 4 policies = 68 JSONL decisions. Includes private/shared read and write, disclosure recipient binding, co-owned layout, conflicting and stale grants, unauthentic grant, unknown owner set, exact and mismatched/revoked delegation, plus emergency release/cancel. Candidate command: `python -B run_candidate.py results/run-01/RAW.jsonl`. Independent audit command: `python -B audit.py results/run-01/RAW.jsonl results/run-01/AUDIT.json`.
- **D:** Independent literal-table audit returned `PASS_METHOD_SCOPED`, 68 rows, errors=0, exact delegated progress=true, effect receipts=0. The audit's `unauthorized_admissions_joint` summary counter is zero for its seven named negative controls; the independent full 68-row literal table additionally rejects both `shared_read_a_only` and `shared_a_only` for joint/delegated modes. Per policy, 17 rows: requester-only admitted 16; all-owner conjunction 7; scoped delegation 8; deny-all 2. The two deny-all admissions are the separate release/cancel safety lane. The requester-only count includes its intentional co-owner boundary failures. All 68 rows report `effect_applied=false` and `effect_verified=false`.
- **C:** Native application/OS ACLs or a human handoff may handle the real boundary more simply; this fixture cannot establish co-ownership or a human's wishes.
- **U:** All owners, permissions, authenticity, generations and delegations were hand-authored. The run tested admission logic, not an actual effect oracle against a real resource. No human consent, ownership discovery, race/concurrency, GUI behavior, system integration, legal conclusion, or product safety is established.

## Construction and integrity

TDD construction: 12/12 tests pass. The initial behavior suite on the deny-all stub produced six expected assertion failures; after implementation and correction of one test whose expectation incorrectly included deny-all, all behavior tests passed. The separate audit suite rejected unsafe admission, permission-as-effect-receipt, row loss and order mutation. Frozen source hashes were checked against `FREEZE.json` before candidate execution; raw and audit are separate files and have distinct recorded hashes below.

The independent auditor does not import `candidate.py`; it uses a separately hand-written expected decision table. This is still a finite synthetic consistency check, not evidence that the fixture captures real owner policy.

## Runtime and resource boundary

CPython 3.12.10 on Windows 11 build 26200, standard library only. The repository's latest main at pre-execution was `043ff4bd321ddf89cc3ced0e74f63435bda093f0`; source is standalone scratch code and does not depend on main. Docker context was `desktop-linux`, but bounded `docker info` timed out, so no container ran. No daemon/container was started, inspected or altered. No GPU, model, network call, human participant, GUI, OS input, real shared resource, or external effect was used.

## SHA-256

| File | SHA-256 |
|---|---|
| `FREEZE.json` | `4e907f7c613e1170d70b84c29b9112509fd3fbffb347c77002741447f3415009` |
| `PREEXEC.json` | `18c092abd8028306c462f410786eb8ec887d34435e6a2772175d79a7bedc342c` |
| `PLAN.md` | `5c48a1ee323cc0f1f70503360a9031e687d92ff612a9e4a906dbf2335de59b1a` |
| `fixtures.py` | `b17161dc730c41469fbe8d9091d5438ece1b576818709de5c98e1cd1ff31312d` |
| `candidate.py` | `eeeb88a79915d3d1f340e662bf3fa6becb112a78f2facd0ab4b6c4dc18f7269e` |
| `audit.py` | `cd9dd28d3ac74f0c55eb20c71592e7f824bbe9398228d7835877475b4e1e970b` |
| `run_candidate.py` | `21d8c0251b0fefacd718bc458edebfca5f39de3f48ed5e510b6fb147141c8a53` |
| `test_t0.py` | `30f78ca477dabd84428ef34821d0e8c77f573fdbfccf0da39a2766590a027458` |
| `test_audit.py` | `2e0bae845f727bc675957f5ce097df9295c90e3a9ca0edb4d7ed650abcb22db5` |
| `results/run-01/RAW.jsonl` | `6ecda141e2c002acc0bae62ec52ff6e6c0cbd34c6fe0c7038a34f26fc18b3823` |
| `results/run-01/AUDIT.json` | `43ee40c63c1dd86b2a955f02d6ebb590cf07c9a9d6d63b8c46fb68317c908369` |

The hash values above cover the files as run; `REPORT.md` is a post-run narrative and is not an input to the freeze or audit. The evidence bundle is being preserved at `research/analysis/joint_authority_5805_t0_exploratory/`; publication does not upgrade its exploratory status.
