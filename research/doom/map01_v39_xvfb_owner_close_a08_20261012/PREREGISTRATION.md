# A08 preregistration - current-main owner close on Xvfb

**H.** With complete exact-current-main sources, V4->V3->V12 admits one `a` key on a focused Xvfb client; wrapper close emits a matching KeyRelease, verifies empty server state, records verified `owner_release(reason=close)`, and stops its thread.

**T.** One isolated TCP-disabled Xvfb display `:130`; one down; assert client KeyPress; close wrapper; assert client KeyRelease, observer key-up, owner terminal record, and stopped thread.

**D.** PASS_METHOD_SCOPED only if all frozen-source digests match and raw-only audit passes all event, server-state, terminal receipt, stopped-thread, and Xvfb exit checks. Setup/incomplete trace is STOP; complete semantic mismatch is FAIL. Candidate once, auditor once if raw exists.

**C.** Synthetic X server and owner-only shutdown. No game, desktop application, OS keyboard, model, private live allocation, or task effect.

**U.** Does not establish physical key state or application consumption, timing distribution, feedback usefulness, threat response, recovery, or MAP01 completion.

Base current main: `f185a9059d485a4f8d5a65e9e7f6782897f67eae`. A07's `input_owner_v10.py` import omission is repaired in this new source freeze; A07 remains unchanged.
