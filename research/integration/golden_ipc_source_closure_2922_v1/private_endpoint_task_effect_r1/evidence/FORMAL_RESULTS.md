# Issue #4924 — Chromium fixture task effect

## Disposition

**PASS_CHROMIUM_FIXTURE_TASK_EFFECT_SCOPED** for the single frozen allocation. The pre-registered one-shot GUI program submitted the exact token from the same session's `ready` event; the saved bytes and independent evaluator both matched.

This result advances only the synthetic Chromium fixture boundary. It does not close Issue #4924 or establish a general desktop capability.

## H / T / D / C / U

- **H:** After the historical session CLI emits `ready`, one bounded Chromium program can visit its session-owned private fixture, enter the exact per-seed token announced by that event, submit it, and produce an exact-match file.
- **T:** One fresh session, allocation `issue2922-chromium-task-effect-20260928-r1`, seed `992928`; historical source commit `01349d7bc76e5635f5568c53ffeec4d9ff49abb1`; image `sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393` (`linux/arm64`, CPython 3.11.2). Source hashes were checked before CLI launch. The only submitted executor program was the frozen nine-step Ctrl+L → URL → READY → token → Tab → Return → SAVED → observe sequence, with a 20-second validity window.
- **D:** Container exit 0; one program accepted and completed 9/9 steps; 37 input-admission events; release verified with `keys_down=[]). Four observations contained `AI FORM READY`; two contained `AI FORM SAVED`. The ready token was `t992928`. Retained `submitted.txt` bytes were exactly `value=t992928`; the independent evaluator returned `success=true`, `actual={"value":["t992928"]}`. A separate network-disabled audit container returned `PASS_CHROMIUM_FIXTURE_TASK_EFFECT_SCOPED`, errors=[]; the audit mutation suite passed 7/7.
- **C:** One synthetic local form, one seed/session, one pinned arm64 container. The token was explicitly supplied by the ready event; this does not test visual task understanding or model utility. No model, host broker, external network, or other application was used. The fixture server's POST counter is not instrumented. No performance, reliability, platform-equivalence, production, or user-task claim is made.
- **U:** Whether a rich-model agent can discover and complete a meaningful task in an actual application, and whether any integrated runtime preserves correctness at useful tempo, remain open.

## Evidence and validation

All 30 formal-output files are retained losslessly in `evidence/raw-evidence-01.tar.gz` (archive SHA-256 `49a28fb2a9a84414c10cbf843bef36aa256942bcaad0e9465e16adfef2bad7fd`). GitHub stores the binary archive as 35 ordered blobs named `raw-evidence-01.tar.gz.partaa` through `partbi`; concatenate in lexical order to reconstruct it. The archive contains 11 PNG observations, 11 `.ait` observations, raw JSONL events/stdout, source receipt, diagnostics, submitted bytes, runner result, audit, and SHA256SUMS. The publication manifest lists each archived file's SHA-256; the runtime SHA256SUMS was independently verified 26/26 on the host. The final PNG was also visually inspected.

The separate raw-only audit recomputes the ready-token/file match, source identities, exact plan, evaluator result, release, and artifact manifest. The 7/7 local mutation tests exercise wrong token, failed release, missing saved rendering, evaluator mismatch, duplicate submission, and altered output bytes.

### Preserved preformal STOP

The first construction preflight stopped at `STOP_PREFORMAL_AUDIT_TEST_SYNTAX` because a mutation-test source edit contained literal backslash-n characters. It started no session, GUI, input, or formal allocation. That exact source and STOP receipt remain preserved in `CONSTRUCTION_STOP_01.json`; the corrected, separately frozen preflight then passed. The formal seed was used only once, after corrected preflight and source readback. No retry or replacement seed was used.

See `FREEZE_V2.json`, `RESULT.json`, `AUDIT.json`, and `PUBLICATION_MANIFEST.json` for the frozen command, raw result, independent audit, and file digests.
