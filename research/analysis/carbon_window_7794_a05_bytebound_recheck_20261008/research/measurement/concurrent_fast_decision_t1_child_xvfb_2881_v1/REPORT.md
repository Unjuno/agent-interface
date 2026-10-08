# Issue #2881 — construction STOP before formal T1 allocation

## Disposition

**STOP_CONSTRUCTION_SCORE_IMAGE_STRING8_TYPE; scientific disposition NONE; formal invocations 0.**

This successor preserves closed #1384's scientific gates and tests only the proposed session/process-lifecycle repair. No #1384 result is rewritten and no formal 12-session block was started.

## H / T / D / C / U

**H.** #1384's preformal XIO teardown stop may be a same-process multi-display lifecycle confound. Running each fresh session in a separate Python child with a private Xvfb should remove that lifecycle confound without changing the selector, 0→40 ms frontier interval, 5 ms cadence, XTEST action, scorer, or decision gates.

**T.** Construction-only lifecycle controls used fresh child/Xvfb pairs at schedule boundaries 0/8/18/20/28/30/40 ms. Then one excluded ACTIVATE_18 matched construction pair used the byte-frozen #1384 candidate/fixture/runner. The parent observed child PID/PGID/SID/start_ticks, Xvfb PID/display/socket, actual child return, process-group residue and socket residue. Formal would have been exactly six matched pairs / twelve sessions only if construction passed.

**D.** Lifecycle construction eventually reached 7/7 clean teardown controls, but the scientific construction pair was ineligible: both sessions returned a caught `TypeError("string argument without an encoding")` before independent scoring. Process cleanup itself was complete 2/2. Formal denominator therefore remains zero. Do not repair the scorer and call that the same one-factor successor.

**C.** The provided Python-Xlib 0.15 environment returns `bytes` for the 1×1 sentinel XGetImage, but `str` for the 120×10 progress/harm scoring XGetImage. The frozen #1384 runner calls `bytes(img.data)` in `count_color`; a latin-1/String8 normalization would be a second source/environment compatibility intervention and was not added to this allocation.

**U.** The process-isolation hypothesis remains scientifically untested. This STOP does not imply the deterministic fast lane is useful/useless, nor fleet-wide Xlib incompatibility. A suitable future allocation under the same Issue may prospectively freeze a separately declared scorer-byte compatibility delta if that change is accepted as necessary; do not silently fold it into this consumed construction.

## Preserved construction chronology

1. `teardown-controls-01`: group SIGTERM at 0 ms left the owned Xvfb as an unreaped zombie (socket absent); STOP retained.
2. `teardown-controls-02`: graceful child handler + group SIGTERM yielded process/socket cleanup 7/7, but simultaneous X-server death produced expected XIO exit1 in every control; STOP retained.
3. `teardown-controls-03`: parent signals the child leader; the handler closes Tk/Xlib then terminates/reaps owned Xvfb. All 7 boundaries: F8 UP before teardown, child/Xvfb same process group, no group member/PID/socket residue, child exit143.
4. `science-pair-01`: baseline and candidate child processes both exit0; Xvfb exit0/socket absent and old cleanup fields true. Both retained result rows contain the same TypeError during score capture; progress/harm scoring is incomplete, terminal F8 evidence is therefore absent, and construction is ineligible.
5. Independent diagnostics: sentinel 1×1 image data is bytes; progress/harm 120×10 data is str. A trace locates the TypeError at frozen runner.py `count_color` line145.

## Source/provenance

Frozen predecessor scientific bytes:
- candidate.py SHA-256 `e1ec191de75e91d22ad4f50e8cab394ff5d6f51c2ea88dc6ad736dcc1c2e2ffd`, Git blob `279a6923bac658d25fb2ecdc916a75c842269cf6`.
- fixture.py SHA-256 `57d457d0d35b62d83b5456f34622c7b46c7b8b6add87bbb6e470333d8cbbe4ab`, Git blob `6e98699ca49c49263e0ea0846932a758ec08b23c`.
- runner.py SHA-256 `41776a062b21fe7b7c1815a626c460c29446341173bb4ea63f27307b2ae4744c`, matching #1384 SOURCE_MAP. The later GitHub file representation has a one-byte publication representation difference; the SOURCE_MAP SHA is the frozen scientific identity used here.

Environment: provided Linux x86_64 execution container, CPython3.13.5, Python-Xlib reports (0,15), Xvfb /usr/bin/Xvfb, Tk8.6. No model/provider/network/real desktop/shared-runtime mutation.

## Raw construction commitments

- teardown-controls-01.json 1135 B SHA256 `24f4dd44dcfd3d4b2932cfc051916bbc3c4980ab47fddc4a4c9697f8f3f2f676`
- teardown-controls-02.json 6539 B SHA256 `b5283b91ea9edbcfe42e78e45c0e44005441b4819c00c5eb0804e24edb155577`
- teardown-controls-03.json 6175 B SHA256 `c300ec19a6ae414da96cb4b7dd3d143f94680dbd23e632db8911ebd225c94303`
- science-pair-01.json 13346 B SHA256 `7ae44e26da8187668bc54e864ff4fe093ec912cef8646069dbc97331f2263dbd`
- trace-session-01.log 507 B SHA256 `9162a546c13534873ef4a2869b102025666e92b311fab9da0da784d248a48812`
- score-image-type-probe-01.log 537 B SHA256 `c65ce0ab99112daacb8345c56de76b4f798de5c4344391c43532c8685b4a2508`

These hashes bind the conversation-local raw construction files; this report does not claim that every primitive byte is hosted on GitHub.
