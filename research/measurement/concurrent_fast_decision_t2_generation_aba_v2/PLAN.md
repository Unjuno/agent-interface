# Issue #1460 fresh allocation v2 — T2 generation ABA guard

Historical #1460 comment 5728762210 claimed a local construction at formal0 but no remote branch/freeze/result exists. This fresh allocation does not reuse that allocation identity or any hidden local rows.

## H
A stale local decision prepared in generation g1 must remain invalid after frontier handback closes g1 and a later request opens g2, even when observable state returns to CLEAR. Binding final admission to the runtime-owned generation prevents this ABA escape; a state-only comparator does not.

## T
Standard-library only. Candidate, independent history oracle, unsafe state-only comparator and fixed deterministic generator. Seed 145920260918012. Exactly 200,000 traces over scopes A/B/C/D: ten classes ×20,000 each. ABA_CLEAR and ABA_BOUNCE are the 40,000 explicit stale-generation stress traces. Formal command exactly once: `python -B runner.py --out FORMAL.json`, followed read-only by `python -B audit.py FORMAL.json --out AUDIT.json`.

Construction is excluded: py_compile and 6 unit methods only; no formal rows. No model/provider/GUI/X11/network/task input/runtime mutation.

## D
PASS_T2_GENERATION_ABA_GUARD_SCOPED iff candidate/oracle result+state mismatches=0; all40,000 ABA stale attempts produce zero candidate effects; state-only comparator produces stale effects; all20,000 fresh g2 CLEAR traces admit; WATCH/HARD/ordinary_authority=false effects=0; replay/cross-scope/forged-generation/duplicate-return controls fail closed; independent audit and source integrity pass; formal1/reruns0/replacements0/tuning0.

FAIL_T2_GENERATION_ABA_ESCAPE on any old-generation effect after later generation opens. FAIL_T2_GENERATION_OVERINVALIDATION on complete fresh-current CLEAR rejection. FAIL_INTEGRITY on source/schedule/audit contradiction.

## C
A production ABI may combine generation with intent/session/owner identities. This tests the semantic need for non-rebindable generation identity, not a final field layout. Receipt drain and physical actuation cancellation are separate questions.

## U / stop
Synthetic state-machine composition only. No provider/model latency, task utility, X11 physical edge, MAP01, token, human-tempo or production claim. Stop after this one frozen formal result and audit.
