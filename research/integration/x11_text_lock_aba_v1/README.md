# Mid-text Caps Lock ABA: retained result and exact-value boundary

Issue #4038; scientific predecessor #4003 / PR #4019. **Retrospective evidence delivery**, not a fresh GUI experiment or GitHub preregistration. The previous conversation executed `x11-text-lock-aba-20260922-01` after a local source freeze at 2026-09-21T21:11:43.311705Z; GitHub writes were then unavailable. All 199 original files and their first outcomes are unchanged, including that historical publication STOP. This continuation revalidates and publishes them, with zero formal/GUI reruns.

## H / T / D / C / U

**H:** Boundary Caps Lock equality cannot identify an OFF/ON/OFF transition during text emission. Completed operations and neutral release do not alone establish exact application text. A reporting-only, identity-bound post-action value comparison can detect the mismatch, not prevent or undo it.

**T:** Five schedules, three repetitions each: 15 fresh ordinary Tk Entry sessions in three fixed, authenticated, TCP-disabled private Xvfb batches; requested text `aB2`. Actual XTEST input uses unchanged backend methods. The documented AST loader omits one unused core-contract import; character-boundary instrumentation changes only private fixture lock state and collects evidence. Five excluded construction sessions use `cD3`. Complete source, full key events, native XKB samples, independent observer snapshots, values, releases, IPC, process/server exits, construction incidents and freeze are retained. Public CLI/core admission is not exercised.

**D:** `PASS_LOCK_ABA_BOUNDARY_SCOPED`, at the original finite scope:

| Schedule | Before / after lock | Actual text | Repetitions |
|---|---|---|---:|
| STABLE_OFF | OFF / OFF | aB2 | 3 |
| LOCK_STAYS_ON | OFF / ON | Ab2 | 3 |
| ABA_WHOLE | OFF / OFF | Ab2 | 3 |
| ABA_MIDDLE | OFF / OFF | ab2 | 3 |
| LOCK_AFTER_TEXT | OFF / ON | aB2 | 3 |

An explicitly authored completion-only comparison makes nine false exact-text claims; a boundary-equality comparison makes six. The retained audit field `backend_false_claims` names the first comparison; **the upstream backend itself is not alleged to declare task success**. Reporting-only exact-value decisions are 6 PASS, 9 FAIL, and 30 HOLD for missing/foreign evidence across 45 views. All decision flags deny input and replay authority. All original execution/release/cleanup checks passed. The unchanged raw-only auditor reports 2,236 checks, zero errors, 13 rejecting mutation controls; 15 unit methods pass.

**C:** Supplied Linux x86_64 execution container, CPython 3.13.5, Tk 8.6.16, Python-Xlib 0.15. No Docker/OrbStack engine or image identity is available; no engine replication is claimed. Only private fixture input; no model/provider, host desktop, clipboard, installation or experiment-network use. Exact backend Git blob: `9cae101a219348077668c8fc086acf8e13154afe`.

**U:** Directed finite coverage, not a natural error rate. One cooperative application and US layout; no general GUI/IME behavior, prevention, rollback, model utility, performance or production qualification. Same-author separately implemented audit is not external human review. A correct value at one sample does not establish future stability or authenticate the application.

## Concrete integration decision

For #2789's result/recovery boundary, do not promote input completion, release, or matching modifier endpoints into exact-text success. A failed postcondition also does not permit automatic unlock, retyping, undo or action replay. The next real integration must bind requested text, target identity and application effect in its own supported path; this research does not implement that path or complete the global ROADMAP.

## Evidence layout and integrity

`candidate.py`, `FREEZE.json` and `AUDIT.json` are byte-identical original files. `CAPSULE.json` binds 14 binary parts of one 80,768-byte XZ file map, SHA-256 `464a793f14abceef3804aa5776a1d2ff4fa2412bc4479ea20553e1708857976a`.

`unpack.py` validates bounded framing, every part and member hash, counts and paths before creating a fresh destination. It restores 209 files / 931,024 bytes without importing or executing them:

- `original/`: all 199 original files / 914,394 bytes, including full `PLAN.md` (H/T/D/C/U and variable/unit table), Japanese `REPORT.md`, runner, app, native state source/binary, backend, audit/tests, all raw evidence and 198-entry manifest.
- `continuation/`: ten new verification/helper/log/incident files. The first publication helper exited 1 because it over-required byte equality of corruption-report exception messages containing randomized temp paths. All underlying checks passed. This helper failure remains recorded; original evidence was not altered and no new Issue was made for it.

Original supplied ZIP SHA-256: `2d82c2105b6a394e3603005701c85bce39134154c163c7417e57787a893c384f`. Member bytes, not ZIP container bytes, are reconstructed. Original audit SHA-256: `593b9f4a2b30e6dafcfa517ed83d5bc5f96ef913421b1d0084a5e5ab718fd393`.

## Read-only reproduction

Use a fresh destination with an existing parent. Do not execute consumed formal commands in FREEZE or the archived runner. Offline audit uses Python standard library; `test_contract.py` additionally imports installed Python-Xlib through the exact loader but does not open a display. Do not use Python -O.

```sh
python -B research/integration/x11_text_lock_aba_v1/test_unpack.py
python -B research/integration/x11_text_lock_aba_v1/unpack.py /tmp/aba4038-review
cd /tmp/aba4038-review/original
sha256sum -c SHA256SUMS
python -B audit.py formal-01 --out /tmp/aba4038-audit.json
cmp AUDIT.json /tmp/aba4038-audit.json
python -B test_audit.py formal-01 --out /tmp/aba4038-controls.json
python -B test_contract.py
```

`VALIDATION.json` records actual local subprocess exits: byte-identical audit, 13 mutation rejections, 15 original unit methods and nine restoration tests (eight refusal controls). Control exception paths vary with temporary directories; their JSON is not claimed byte-identical. Hashes are integrity commitments, not authentication. Whole-repository CI and external review remain separate gates.

## Delivery roadmap

Original source/raw revalidation completed; lossless restoration and packaging controls completed. Next: exact Git-object readback, additive evidence PR, exact-head checks/review, qualified merge and main readback. Remove only the owned branch after verified integration and dependency checks through a supported operation. No prior result, shared runtime, workflow, root index or other branch is modified.
