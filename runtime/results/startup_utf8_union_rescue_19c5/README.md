# Startup / UTF-8 interaction counterexample rescue

Original source `19c5139fc8df6c838e071026d96ae0f7aaa477c0`, old delivery PR #6978. Rescue base `12e4c1eba` (Git parent of the rescue commit).

The 238-file `research/integration/primary_startup_utf8_union_57_20261003_01a0ff32` packet is byte-identical to its original Git tree. No old runtime, workflow or approval was adopted. Historical frozen Windows tests report 51/51 affected methods, but the actual four-case diagnostic preserves **FAIL_FIRST_DECODER_ERROR_MASKED** in malformed-then-stream: later input error masks the first decoder error. Four custody cases and three diagnostics pass; one diagnostic fails. Original cp932 reader failure and reply-enrichment reader failure remain untouched. No original allocation is retried.

Fresh readonly checks: 237/237 public length/SHA256 manifest entries match. `verify_saved.py` loads the published four case bundles and literal pure classification/control portion of the original oracle, without its top-level source-pin checks, old-platform PID probes, or historical writer. In normal and Python -O mode it retains the same four-custody/three-diagnostic-pass/one-diagnostic-fail classification and rejects all eight copied controls. This checks saved-data semantics, not original execution authenticity or current process absence. It preserves the scope rather than pretending to execute the original auditor.

The first new reader run failed because healthy second-input is published as `.raw.txt` while invalid bytes use `.raw.hex`. `readonly-first-failure.log` retains that error. The only reader repair selects the actual published representation; the scientific criterion, packet and classification functions are unchanged. `readonly.log` is the subsequent successful saved-data check.

Fresh current-maintained stdio/UTF8/relay suites passed 48/48, zero failure, skip or cancellation on macOS Node26.7 (`node.log`). That is not a replay of the frozen Windows 51-method union or four native relay fixtures, and it does not establish that current main has repaired the retained diagnostic.

H: retain the first combined-source counterexample without erasing failed diagnostics.
T: exact Git packet comparison, public manifest and literal saved classification plus eight controls; current maintained suites separately.
D: 238 exact files; 237 matching entries; saved diagnosis remains FAIL; current suites48/48.
C: historical isolated union differs from current main; manifest is consistency not original authentication.
U: no original producer/auditor replay, fresh native relay case allocation, formal/backend/model/task/timing certificate or production fix.

Local CI completed with exit0 and `LOCAL_CI_SUMMARY: steps=43 failures=[]`, recorded in `local-ci.log`. OrbStack Docker image inspection currently fails opening a daemon blob with operation-not-supported; no reset/prune/pull or shared resource was used.
