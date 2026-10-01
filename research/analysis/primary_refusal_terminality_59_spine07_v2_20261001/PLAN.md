# #5693 spine-07 malformed-envelope terminality successor v2

Status: construction candidate only. No candidate, auditor, Docker container, or live effect has run. Not a scientific result or Docker lease.

## H / T / D / C / U

**H.** In exact spine-07 source, response-envelope extraction ran after the transport catch. A malformed reply could throw before STOP latched, allowing a primary that caught the exception to dispatch again. This candidate moves `read(reply)` and `isError` extraction inside the existing fail-and-latch boundary, preserving the original exception and reply.

**T.** Four deterministic mock cases in one candidate invocation: malformed envelope, valid response, declared refusal, and transport throw. The malformed and transport cases attempt one further effectful dispatch and public close. A separate raw-only auditor runs once iff candidate exits 0. No MCP, game, GUI, model, X11, GPU, or OS input.

**D.** PASS only if malformed and transport cases latch STOP before exception propagation, reject the second effectful attempt locally (host effectful-call count exactly 1), and allow close; valid and declared-refusal controls remain usable without STOP; exact source identity and raw rows pass the independent auditor. Any second effectful call is `FAIL_UNCERTAIN_DELIVERY_REPLAY`. Provenance, image, queue, or audit failure is STOP.

**C.** Upstream is main-preserved spine-07 blob `b2f27b6cda362db24e906090f33c4813d60f2867`, originally frozen at PR #5639 head `83367dc9299237733112d6eef4b0e6ce18781ef8`. Formal execution requires a fresh exclusive lane, exact cached digest-pinned Node image/platform, exact current-main/source hashes, and clean resource/output gates. Candidate once; raw-only auditor once only if candidate exit is exactly 0. No retry or engine substitution.

**U.** Synthetic caller boundary only; no real MCP delivery semantics, live refusal, GUI/game task effect, physical release, task success, latency, efficacy, MAP01 or product claim. #59 remains open.

## Formal protocol

Run candidate exactly once in an authorized pinned Node container; preserve stdout/stderr and exit. Only on exit 0, pass exact stdout bytes to one separate raw-only auditor invocation and retain outputs/hashes. No overwrite or retry. This plan confers no allocation or slot.