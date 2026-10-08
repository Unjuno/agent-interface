# Issue #8533 T0 A01 — result

## Disposition

`METHOD_PASS_SCOPED`. Candidate and independent auditor each ran once, with no retries. The auditor validated 12 training examples, 16 held-out test examples, three parity-controlled arms, four truth classes, one unseen tactic, and 94 checks; all 7 mutation controls were rejected. Candidate raw SHA-256: `a921e4ffe24064f005aa1f75e69d876250b7326dd066deca24fc236b1a15412a`.

## Method findings

The truth table separated verified scoped success, dispatch-only false success, partial effect, and UNKNOWN. Every test tactic crossed all four truth classes, including `social_proof`, which was not used in training. Training and test case, layout, receipt, and example IDs were disjoint. Across the tactic-inoculation, evidence-first, and neutral arms, each example retained identical factual evidence and feedback with an 80-word content budget and 60-second planned exposure. Test prompts contained no truth or tactic labels, and the truth oracle remained separately joined by case ID. UNKNOWN evidence did not become completed.

## Scope and limits

This validates only authored vignette truth, content parity metadata, and holdout bookkeeping. It does not show tactic inoculation improves delayed human discrimination, transfers to real outputs, reduces false acceptance without increasing false rejection, or supports any security/product claim. The word budget and exposure time are metadata; no participant read or timed the material. No blinded human review was conducted, so automated oracle validation does not establish that all wording is unambiguous or accessible. No participant, model, GUI, private file, account approval, network, or external effect was used; authority remains `NONE`. T1 requires separate consent and allocation.

## Provenance

Preregistration: [Issue #8533 comment](https://github.com/Unjuno/agent-interface/issues/8533). Frozen source commit: `dd83fb1b1268f2495474a7cc1695a587b9d40cb2`; base main: `4758a95cd4a0aaa78e9cdc9d774f298d4ccf0e36`. Raw output, independent audit, command logs, exits, timestamps, and hashes are under `results/`. See [FREEZE.json](FREEZE.json), [PLAN.md](PLAN.md), [spec.json](spec.json), and [SHA256SUMS.json](SHA256SUMS.json).
