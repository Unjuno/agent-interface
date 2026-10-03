# WSLc T7 stopped audit evidence rescue

Original source `684831240f9848e850736781edb98322949e8d8a`, old delivery #6983, study #6975 / predecessor #5309. The 11-file packet `research/analysis/wslc_retained_audit_5309_t7_20261003` is copied byte-identically from Git. No frozen verifier, allocation, candidate, container, or historical verdict was changed or rerun.

The historical WSLc auditor emitted a 432-row receipt but the frozen host gate expects `failed_probe_yield_fallback_wrong_target`, while the actual receipt contains `failed_probe_yield_wrong_target: 0`. The scientific outcome remains **STOP_HOST_RECEIPT_SCHEMA_MISMATCH**, not PASS.

Fresh macOS Python3.14 readonly checks: the original six unit tests pass normal and -O, but use synthetic expected-schema data and do not establish actual receipt acceptance. Running the unchanged host verifier against the saved receipt exits1 with the exact missing-field ValueError; `receipt-failure.log` preserves it. No old WSLc container/auditor invocation was repeated.

Fresh manifest check FAILED: all six recorded published artifact lengths/SHA256s differ from their declarations (`manifest-failure.log`). Source Git blob and restored file agree, so this mismatch predates rescue. Readonly LF-normalization did not reconcile the hashes (`newline-hypothesis.log`). Every published record instead has one additional terminal CRLF (2bytes): removing only those bytes in memory exactly matches each declared length/hash (`suffix-diagnosis.log`). This is a bounded publication-byte explanation, not permission to modify original records or authenticate original execution. All original files and manifests retain their exact bytes, including that suffix and the STOP.

H: stopped audit and publication mismatch remain useful historical integration evidence.
T: exact Git packet comparison, unchanged six unit tests, saved receipt rejection and recorded-byte diagnosis.
D: 11 exact files; unit6/6; actual saved receipt rejected; raw manifest6/6 mismatched, six in-memory suffix projections match.
C: unit PASS is not receipt PASS; suffix relation is not execution authentication; WSLc allocation remains consumed.
U: no new candidate/auditor/container/formal execution, verifier repair, Windows runtime, speed/memory/backend/task or product certificate.

Local CI is recorded separately in `local-ci.log`. Current macOS OrbStack image loading has an operation-not-supported daemon-blob STOP; no reset, prune, pull or shared VM was used.
