# #4432 shared experimental reader hash-reuse promotion

Disposition: **PASS_SHARED_SOURCE_REGRESSION_SCOPED**.

This is the shared-source adoption regression for the exact executable candidate already characterized under #4399. It does not rerun #4399's consumed performance or CLI-comparison allocations and does not claim production inbox/model/task benefit.

## Provenance

- intake/main: `3666992ab2b5e1b41b159b361d1c690d8e720fdf`
- original reader Git blob: `ea72c166c2cea511ea91031dfbb14563fe4e3245`
- promoted reader Git blob: `3b4ac9af076bdc5dee94e09cbab22b17bc45173a`
- new regression Git blob: `9036f8815f35867a6b874b32323bf202de40ef6b`
- inherited reader tests: `486f31fb6600b8563d8cc7f34a1fbdff1d958f5a`
- inherited CLI test: `c5b6b915fc484a951507fe87b83993662412c6ef`
- DeliveryLedger dependency: `fb50be9d4d821a7836e6a0158c53a983f0f91df5`
- #4399 public candidate blob: `1b1d8b4180215e76e76b4751626113f6a603cf20`

After removing #4399's two provenance-only header comments and normalizing one explanatory comment, the promoted reader is executable-text identical to that publicly frozen candidate.

## Formal regression

The prospectively amended gate was posted to #4432 before this invocation. Exactly one test invocation was performed:

```
python -B -m unittest -v   research.integration.event_inbox_reader_v1.test_reader   research.integration.event_inbox_reader_v1.test_cli   research.integration.event_inbox_reader_v1.test_hash_reuse_p7c4
```

Result: **13/13 methods passed**, internal test-process exit `0`, no formal retry/replacement/source change.

Saved internal execution receipt:
- stderr bytes: 2274
- stderr SHA-256: `513c73426c0e1ba776660b335daa3648def2736d90226b65ff54e6492743de49`
- stdout bytes: 0
- stdout SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

All five source/dependency Git blob identities were checked immediately before the test and again afterward and remained exact.

### Execution-envelope incident

The surrounding local execution tool reported status 1 **after** the completed test command, accompanied by `TERM environment variable not set`. The test command's own captured exit code is 0 and its complete unittest output ends with `Ran 13 tests ... OK`. The allocation was not rerun. This envelope incident is retained separately from the completed regression disposition and is not evidence of a reader/test failure.

## H / T / D / C / U

**H:** reuse the freshly verified SHA-256 state only within one `read_pending` call, while every new invocation still reads the current bounded file and freshly validates the consumed prefix.

**T:** one shared-source regression invocation against exact branch bytes; existing reader and CLI tests plus seven new hash-lifetime/refusal regressions. #4399 supplies the already-retained independent equivalence/CLI evidence for the identical executable candidate. No performance rerun.

**D:** PASS because all 13 tests passed, changed-prefix refusal and blocked/incomplete cursor behavior are retained, interleaved streams show no shared digest state, and all source blobs remain unchanged. Exact-head CI/review remains a separate merge gate.

**C:** incremental hashlib semantics over the one-call immutable `bytes` snapshot explain the result. Full-file reading, JSON parsing, newline counting, and cross-call prefix validation are unchanged.

**U:** experimental passive reader only; no live producer concurrency, model receipt/ACK, task effect, token/end-to-end latency, cross-platform or product claim. Same-author testing is not external review.

## Publication incident

Before formal execution, GitHub accepted the reader and regression writes, then blocked the next attempted duplicate baseline/evidence publication on safety-status grounds. No blocked payload was resent through a different path or encoding. The baseline already exists on main, and the retained #4399 public candidate/evidence remains the comparison source.

