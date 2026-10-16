# Evidence retention boundary

GitHub retains the frozen 015 harness, audit, preregistration, schedule, REPORT, all 20 per-case endpoint summaries/result hashes, corruption-control outcomes, and the additive correction to Issue #321's visual-selection evidence label.

The exact full local archive is attached to the conversation as `inkscape_preinput_visual_guard_v1_complete.tar.xz`:

- bytes: 1,106,800
- SHA-256: `9b8ee60e6dd3f5e88bbb5ceaae3065ef6825a1d9e78d007b5538137ff8af6a1a`
- package manifest rows: 310
- fresh-extraction audit stdout SHA-256: `0d34e02e47c31ebe9d17516b9ccdf982c9c96930818a3348eb2c6033a6b17318` (identical to original measured audit output)

Raw measured PNG bytes and construction PNG bytes are **not claimed GitHub-retained** in this PR. The GitHub result file binds every first measured result row by SHA-256; full visual/pixel recomputation requires the local archive.

Predecessor 014 remains stopped and unpooled. Its exact frozen `run_case.py` was reconstructible byte-for-byte from the retained successor workspace and matches the preregistered 014 SHA-256 `58a8df7a30dbbe1a89453c5ea7b3026add7005e6ddcd6b0be21cddc008ac4234`; Issue #327 contains the stopped-block outcome/failure record. No 014 row contributes to the 015 decision.
