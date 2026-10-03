# Runtime receipt-start lower bound — #5215

The runtime accepts a matching ExecutionReceipt whose started_ns precedes the successfully accepted begin_execution call. Refuse that receipt before changing any lifecycle state. Equality/later starts remain valid; a refused receipt can be followed by a current receipt or verified cancellation.

This follow-up adds two lines to record_execution and eight regression methods. It reuses execution_started_ns from pending #6892 exact head d06e636a8c35715d371dc6ba00632aab4b3bad3c, set only after successful begin. The dependency's four runtime lines and six cancellation methods are unchanged. No second clock state is added. Delivery to main requires the valid delivery of that dependency and this proposal's separate content and exact-current-tree agreement; a draft stacked PR alone does not adopt the repair.

The earlier ordinary characterization is retained unchanged in merged #6878 at 7fcdb8efd1c4fe6e4cb7b330d9a17202b2b69b45, package kernel-begin-causality-01a0ff58, SHA256SUMS eb394b3b44ce998403e52b507fa47a09e1f01cb6701ec5c939677d66e5cfc27d. Its independent 432-row raw audit established 60 matching pre-begin acceptances versus zero for its isolated candidate. Those historical producer/mutation runs are not repeated here. This package contains fresh ordinary runtime regressions and directed source corruption controls, not a new scientific matrix or formal allocation.

| Check | Observed result |
|---|---|
| New regressions on unmodified dependency | 8 methods, 6 expected missing-ContractError failures, exit1 |
| Combined kernel discovery after the two-line fix | 35/35 methods, exit0 |
| Same combined discovery with -O | 35/35 methods, exit0 |
| Missing/reversed guard controls | Four specified assertion failures each, no errors |
| Equality rejection control | One specified ContractError, no unrelated error |
| Assignment before refusal control | Four state identity failures, no errors |

Tests retain equality/later receipt admission, including receipt timestamps after lease expiry; the begin admission remains before expiry. No execution cutoff is inferred from late receipts. Original command/manifest/lease/observation/surface/action-count checks, missing begin refusal, rejected-first-begin and duplicate-begin preservation remain required. All lifecycle attributes retain identity on pre-begin-start refusal. The full discovery covers the 21 merged single-begin methods, six #6892 cancellation methods and eight new receipt methods. Hosted workflow coverage is not assumed.

SOURCE.json pins all six original dependency Git blobs before tests; exact bytes are in source/*.py.txt. candidate_lifecycle.py.txt and regressions.py.txt match the two proposed runtime files. PLAN.md was written before the original expected failures. The four mutation sources/results and MUTATIONS.json retain directed child exits and expected failure classifications. prepare/run/check scripts are retained as .txt so evidence files are not silently included in runtime test discovery. Their original private work layout is documented by their source; reproduce unit behavior with the commands below, rather than executing the archival helper .txt files in place.

```powershell
python -B -m unittest discover -s runtime/kernel -p 'test_*.py' -v
python -B -O -m unittest discover -s runtime/kernel -p 'test_*.py' -v
```

logs/*.receipt.json record UTC intervals, exact command/version, child exits and original/published log hashes. Only private traceback path prefixes are redacted; original bytes remain in the owner's private work. Publication does not change source, test outcomes or receipt timings. SHA256SUMS covers every published file except itself. The scoped .gitattributes preserves bytes rather than normalizing Windows logs. Hash identities bind retained bytes; they do not establish clock provenance or authenticity of arbitrary reports.

Scope: sequential trusted typed records in one comparable clock, finite consistency regressions. Physical release, backend/OS/GUI/model execution, public-field mutation protection, concurrency, task effect, latency and product/scientific success are unverified. No workflow, contract, backend or predecessor evidence was edited. No input/GPU/container/model/shared resource or formal allocation was used. #5215 remains broader than this one boundary.
