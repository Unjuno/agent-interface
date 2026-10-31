# Trace actual OCR runner calls during bounded Calc recovery

The previous Calc OCR packet retained a legacy `command` field saying `--psm 11` even though its crop-mode source constructed `--psm 7`. The historical evidence remains unchanged. This change adds a small reusable `OcrAttemptRecorder` for synchronous OCR runners: it records a copy of the arguments actually passed to the runner, input/output SHA-256 hashes, timing, return code or exception type, and re-raises failures without retry. It does not retain raw image bytes in its trace, enforce the timeout, grant input authority, or prove the operating system executed a particular command. The caller owns trace persistence; a missing trace is unknown.

Two prospectively fixed, isolated WSLc Calc trials used identical code and inputs. Both first produced the original stale-reference `SAFE_YIELD / effect_unavailable`, with the entry unreplayed. Their only condition difference was the recovery OCR runner:

| Trial | OCR condition | Recorded OCR runner calls | Recovery | Saved FODS |
|---|---|---:|---|---|
| e06 | injected `TimeoutExpired` before an external OCR process | 1, timeout | unknown; no new Save | byte-identical blank |
| e07 | real OCR subprocesses | 2, returned 0 | fresh cue filled; one newly guarded Save | exactly A1=329, A2=517 |

The recorder captured the crop calls with `--psm 7`, and their input/output hashes match the independently reconstructed crop images and retained TSV/stderr bytes. The copied cue's old `command` field still says `--psm 11`; the separate call trace corrects that evidence gap for this caller, not for historical packets or other callers. The injected timeout was immediate and does **not** demonstrate a real OCR process hanging for one second. Both original entry releases, the e07 Save release, final close and independent input readback were neutral; both containers exited. Independent XML parsing confirmed all populated direct cells in e07. The old method remained `SAFE_YIELD`, `task_success=null` and replay forbidden.

Each live trial used one `gpt-6.1-sol` low call (12,197 input and 78 output tokens, cached input 0); there was no model retry or schema preflight. One fixed-order pair, fixed reviewed cell geometry, known expected values and an injected failure do not establish general OCR accuracy, automatic production recovery, a hard deadline or MAP01 completion. The recorder is a reusable research helper; its use in the Calc recovery remains an experimental caller. Issue 57 remains open.

`public.zip` retains candidate helper/test, frozen conditions and source hashes, fresh screenshots, per-attempt trace, OCR TSVs and stderr, owner/Save receipts, saved FODS and cleanup. Private model protocol journals are hash-indexed. `python audit.py` checks archive integrity, actual wrapper arguments and output hashes, independently reconstructs cropped PNG hashes, parses OCR TSVs and saved FODS, verifies no entry replay and bounded recorded attempts, and checks release/cleanup. The separate legacy command field is explicitly checked and not rewritten. Full source/image bytes and OS-level process tracing are not included.
