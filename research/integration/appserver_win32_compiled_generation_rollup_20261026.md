# AppServer to supervised Win32 compiled caller R01–R07

Date: 2026-10-26. Source base: `41ac34a227d316c842999143c629ddeeedf51ce8`.

## Result

R07 is the first end-to-end live Windows fixture pass joining an actual AppServer image-grounded decision to standard supervised Win32 MCP endpoints and `run_public_compiled`. It passed release, fresh-observation, exact fixture effect, and independent task-oracle checks. R01–R06 are retained as separate failed attempts; none is overwritten or replayed.

| Attempt | Outcome | First terminal issue / evidence |
| --- | --- | --- |
| [R01](appserver_win32_compiled_generation_r01/) | Harness failure | Pre-provider MCP call rejected by the ledger's provider-first contract; no model request or input. Two earlier import/bootstrap errors are separately retained. |
| [R02](appserver_win32_compiled_generation_r02/) | Harness failure | Grounding capture succeeded with a matched generation and 400×180 image; harness read target from the wrong level. No model request or input. |
| [R03](appserver_win32_compiled_generation_r03/) | Provider pass; no input | One completed model turn, 10,273 input / 19 output / 0 reasoning tokens, coordinate `(150,100)`; graph rejected a 15,000 ms budget above the 10,000 ms contract maximum. |
| [R04](appserver_win32_compiled_generation_r04/) | Provider pass; no input | Graph observation failed because recorded MCP calls used a synthetic attempt ID with no provider parent. Receipt had zero transitions and zero dispatch. |
| [R05](appserver_win32_compiled_generation_r05/) | Effect occurred; compiled receipt failed | One dispatch completed with verified release; fixture saved the exact effect; a fresh observation followed. The effect callback returned undeclared fields, so the core rejected its strict verdict schema before task-oracle verification. |
| [R06](appserver_win32_compiled_generation_r06/) | Effect occurred; compiled receipt failed | Same exact fixture effect, verified release, and fresh post-dispatch observation. Core rejected the 86-character evidence reference; the server task oracle was not called. |
| [R07](appserver_win32_compiled_generation_r07/) | **PASS_SCOPED_WIN32_COMPILED_LIVE** | One model-grounded coordinate `(150,90)`; generation matched across provider wait and first execution observation; one dispatch; release verified with no keys/buttons down or unknown; effect observation captured 18.056 ms after dispatch response return; fixture effect and server task oracle both verified for the exact call and target generation. |

## R07 accounting and evidence

- AppServer usage: 10,273 input, 19 output, 0 reasoning output; image-input token count unavailable. Ledger usage status is complete for input/output, while detailed usage is incomplete.
- Independent fixture effect: `{"clicked":true,"saved":true,"text":"office"}`; SHA-256 `5d299e2a8b715688998c41d1bb9502e42abd9c4e536955d5fa8afc9fe9677389`.
- Standard dispatch call: `f31578a16cb54af1b41494fc47edc2f0`; the independent task oracle returned `verified` / `task_success=true`, matching that call ID, operation ID, oracle ID, and target generation.
- The R07 run retains provider protocol records, raw provider ledger, pre-provider grounding request/response bytes, standard-MCP observations and dispatch, native fixture events/effect file, compiled receipt, task-oracle receipt, cleanup receipt, and 56 verified SHA-256 entries. `SHA256SUMS` checks cleanly.
- The fixture process exited with code 0 and the pre-run foreground window was restored.

## Scope boundary

This is one scoped Windows fixture pass. It establishes neither production-application success nor MAP01/live-game control. It does not exercise blocked-I/O recovery, WSLc, or Docker, and it is not an efficiency comparison or reliability estimate. The R01–R06 failures remain important harness and contract findings; preserve them when reusing this path.

The immutable packet contents and conditions are in [R07](appserver_win32_compiled_generation_r07/). The current-source compiled-caller contract regression is implemented on PR #9581.
