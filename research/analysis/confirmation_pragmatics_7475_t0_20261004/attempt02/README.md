# Issue #7475 — T0 synthetic card equivalence audit

## H/T/D/C/U

- **H:** A truthful continuation/completion frame may alter inferred state or scope despite identical explicit action facts. This attempt does not test the human hypothesis.
- **T:** For three synthetic actions, render neutral/framed pairs after freezing underlying facts and a separate answer key. Independently compare displayed facts, status, target, payload, consequence, reversibility, evidence, layout, and response order. Run target/status/control-order corruption controls.
- **D:** PASS_METHOD_SCOPED only if the pre-wording fact/key hashes match, each pair differs only in its framing sentence, answers match the fixed facts, and all three corruptions are rejected.
- **C:** Users may rely on explicit action facts and ignore pragmatic framing. No user response is observed.
- **U:** Synthetic English construction only. No people, UI, accounts, model, action dispatch, approval, or effect. T1 remains separately gated on approval and consent.

## Freeze and result

Source: Issue #7475 and current main `0178fd24e9c317fff40e0fa1952fbe7e8ae01078`. Attempt 01 is retained as a STOP because its key was written after wording was drafted. Attempt 02 then froze `facts.json` and `answer_key.json` at `PREWORDING_LOCK.json` before creating `stimuli.json`; `independent_audit.py` rechecks both frozen hashes. Raw cards and independent result are `candidate_raw.json` and `audit_result.json`.

Run: `python candidate.py` then `python independent_audit.py`.
