# MAP01 recovery mechanics development v2

Status: **FROZEN HARNESS REPAIR; same runtime condition as dev-01.**

Dev-01 run `34971740475` reached real X11 key admission and verified direct release but the posthoc development analyzer falsely reported zero held input. The runtime was not the failure. `input_admission` from the retained owner carries `intent_token` and `key` but no program `id`; dev-01 incorrectly filtered it by `id == program_id`.

V2 changes only retained-input attribution. The program's verified `input_release_transition` batch identifies the program through `release_batch_identifier`; its `(intent_token,key)` set is then matched one-to-one against id-less admissions. Missing, duplicate, unverified or temporally invalid pairs fail closed.

The exact retained dev-01 sample reconstructs `a` as **270.481963–271.000429 ms**. Nine focused container regressions pass, including duplicate/missing/wrong-token/unverified cases. Source SHA-256: analyzer wrapper `64a26d6a65429f33ff9b9b2fc5ed93eebb3f5c712fa26a1b5e36238a83cfff48`; tests `70f6c1fc783b1a7da5480e509f27e12ef2cb2a26eaca1552f630fe1f74b12f90`.

The live dev-02 condition is intentionally unchanged from dev-01: seed 990615, fresh MAP01, 600 ms wait surrogate, coast versus one 240 ms `a` recovery hold followed by coast, 8-point health guard, no model. Dev-01 remains retained failed and is not relabelled.

**H:** the dev-01 runtime mechanics were valid and only attribution was defective. **T:** exact retained regression plus one new no-retry development allocation using the same condition. **D:** PASS only if recovery is directly exposed, coast has zero admission, recovery lowers no-input upper bound, both terminals release empty, scorer misses/leaks are zero and both terminal audits pass. **C:** the same condition may still expose a separate runtime defect. **U:** development mechanics are not useful-control efficacy and do not consume the frozen formal recovery-v2 allocation.
