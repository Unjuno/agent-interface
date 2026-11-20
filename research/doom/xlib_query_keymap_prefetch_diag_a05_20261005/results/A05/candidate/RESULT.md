# A05 result — PASS_QUEUE_PREFETCH_DIAGNOSTIC

One candidate ran after isolated guest setup and exited 0; the raw-only auditor ran once and exited 0 with all 16 checks passing. For both injected edges, the exact expected client key event was present in the serialized Python-Xlib internal queue before `select()`, and the X socket was not readable. The down edge snapshot contained two `MappingNotify` events without `detail` followed by `KeyPress`; the up edge contained `KeyRelease`. `query_keymap()` observed down=true then down=false. Xvfb exited 0.

Environment: Ubuntu 24.04.5 arm64, Python 3.12.3, Python-Xlib 0.33-2, Xvfb package 2:21.1.12-1ubuntu1.8. The raw field for `Xvfb -version` says `Unrecognized option`; the exact version is established by the setup log. Non-fatal unknown-XF86-keysym warnings came from xkbcomp.

This resolves a narrow instrumentation question: a synchronous Python-Xlib keymap query can leave the target key event already queued while `select()` reports no socket readability in this synthetic fixture. It makes A03's missing-event inference invalid, but does not identify the event that caused A03's `AttributeError('detail')`. It does not test V39, a live game/model, task effect, threat response, recovery, input authority, latency, or MAP01.

The isolated guest was stopped after capture. Invocation counts: candidate 1, auditor 1, retries 0. See `RESULT.json`, raw/audit files and `SHA256SUMS` for hashes.

## Posthoc auditor qualification

The original V1 auditor's baseline result is retained unchanged. A subsequent in-memory mutation control found that V1 also accepted a self-consistent change of fixture keycode and matching event details from 38 to 39. This weakens V1's independent identity check. A separate posthoc V2 auditor pins the protocol keycode (`a` = 38 in the pinned fixture), passes the retained raw, and rejects that mutation; its 3 regression tests pass. The candidate was not rerun, and the original raw/V1 audit were not modified. V2 output and source are in `../POSTHOC-AUDIT-V2.json` and `../posthoc/`.
