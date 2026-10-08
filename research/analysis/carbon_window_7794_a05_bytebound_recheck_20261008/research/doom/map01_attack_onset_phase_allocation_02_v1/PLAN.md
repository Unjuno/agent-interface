# Issue #4223, allocation 02 — H/T/D/C/U preregistration

This is a separately identified allocation under the same scientific Issue. Allocation `map01-attack-onset-phase-20260923-01` consumed its one permitted invocation and stopped before the first observation because the locally assembled image omitted its bundled `python_xlib` wheel. This allocation corrects and preflights only the local runtime environment. It does not overwrite, replace, or pool the predecessor allocation or its STOP evidence.

## H — hypothesis

At fixed fixture `map01-threat-contact-v2`, seed 992600, v12 physical-edge route, independent scorer, key `space`, and one 600 ms attack, attack-onset phase may determine whether an independently scored TASK_EFFECT is observed. Compare only 0 ms authored pre-roll (`IMMEDIATE`) with exactly 600 ms input-free pre-roll (`ONE_WINDOW_PREROLL`).

## T — treatment and measurement

- Runtime artifact 10398313098, SHA-256 `522763418610ea10e57e55615fa71e76445200b9f86d208820ea97c77c234f0b`; source base `9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245`.
- Linux x86_64 / CPython 3.13.5; ViZDoom 1.3.0; private TCP-disabled Xvfb/Openbox; ASYNC_SPECTATOR35Hz, skill1, timeout60s.
- v12 `input_owner_v12.py` SHA-256 `b63e8a925a5ff741385fb69b8cf20ac07e01a520f34607778d8d28a0256c1508`; `adapter_contract.py` SHA-256 `ed7e4f00675e79a9ef86984c7c129bb6c3eda64855c6c71821c313c9feb9badf`.
- The final local-wheel image installs the exact bundled `python-xlib==0.33` and its bundled `six==1.17.0` dependency, then passes `import_preflight.py` before formal invocation. The preflight mirrors the entrypoint's module search order, imports the retained session module graph and opens/closes an Xvfb display; it starts no game/session and sends no input. The formal source and scientific conditions are unchanged.
- Formal schedule: four matched pairs / eight fresh restored sessions, counterorder I→P / P→I / I→P / P→I, every session seed992600. Each gets exactly one `space` 600 ms hold; PREROLL adds only 600 ms input-free sleep after the initial observation and before clock/admission.
- Exactly one formal orchestration, reruns/replacements/tuning0. No model/provider calls. Preserve raw scorer chronology, plan/actuation identity, physical DOWN/UP intervals, release neutrality, exits, and source identities. Game tic remains unavailable and is not inferred.

## D — decision

`PASS_ATTACK_ONSET_PHASE_DISCRIMINATES_SCOPED` only if all eight sessions pass process/source/physical/release/integrity gates and independently bound TASK_EFFECT presence differs by arm in at least 3/4 matched pairs. If integrity passes but the discriminator does not, retain `HOLD_ATTACK_ONSET_PHASE_NOT_DISCRIMINATING`. Any runtime/schema, wrong-arm/seed, source/lineage, scorer-authority, pre-down effect, duplicate effect, or non-neutral release issue is FAIL/STOP. No rerun, replacement, or tuning within this allocation.

## C — caveat

Wall-clock pre-roll proxies asynchronous game/AI/render phase. Any discrimination applies only to this fixed exposure; it is not a general attack policy.

## U — prohibited inference

No recovery-vs-coast efficacy, MAP01 clear, model quality, token/latency, population reliability, human-tempo, or production claim.

## Outcome boundary

The predecessor's excluded construction pair and this successor's formal rows remain separate denominators. A runtime/import-only PASS establishes environment readiness only, never gameplay or TASK_EFFECT.
