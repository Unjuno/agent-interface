# Formal result — temporal stream resume allocation 01

Issue: [#4447](https://github.com/Unjuno/agent-interface/issues/4447)

Allocation: `temporal-stream-resume-20260926-01`
Disposition: **HOLD_AUDIT_CONTROL_CANDIDATE_RETURN_CODE**

## H / T / D / C / U

**H:** A pending temporal obligation cannot be resumed correctly from emitted statuses/cursor/tick alone; exact retained-prefix replay into fresh monitors preserves uninterrupted suffix decisions.

**T:** The frozen source schedule specified 24 notification streams, 48 valid cutpoints and six typed corruptions (54 cases), in six sequential batches of nine. Each case used separate prepare, replay-resume and result-only comparator processes. All six Docker batch invocations were made once, in order, after checking the preceding batch receipt. No GUI/X11, model, network experiment or task input was used.

**Observed:** All 54 case subprocesses completed with return code 0; all six Docker outer batch processes exited 0 and reported complete. Candidate replay matched the independently recomputed uninterrupted oracle at **48/48** cutpoints. The result-only comparator disagreed at **40/48** cutpoints. All **6/6** typed corruption cases returned `REFUSE_CHECKPOINT`. The independent raw-only auditor reported `errors=[]`, `rows=54`, `candidate_ok=48`, `comparator_failures=40`, `controls=6`, `batch_files=6`.

**D:** The allocation does **not** meet the frozen formal PASS gate. Ten copied-evidence mutations were attempted; only **9/10** were effectively rejected. The `candidate_rc` mutation changes a retained candidate subprocess return code to 9, but the unchanged auditor still exits 0 with `errors=[]`. This is a material auditor coverage hole: the auditor validates candidate status/suffix/checkpoint but does not validate that candidate subprocess return code. Because the preregistered gate requires at least ten effective corruption rejections, the result remains HOLD; no gate/source tuning or scientific rerun was performed.

**C:** The observed replay/comparator result applies to the exact frozen fixture and schedule only. Replay retains more information and performs more work; this is a sufficiency result, not a performance comparison. The 48 cutpoints are deterministic coverage cells, not independent natural trials. The comparator is an authored diagnostic, not a claim about deployed production behavior.

**U:** Crash/power-loss durability, storage corruption, reconnect completeness, concurrent writers, prefix compaction/GC, authenticated source identity, optimized checkpoint serialization, live application effects, model utility, latency/token savings and production integration remain untested.

## Execution and evidence provenance

The Docker source was read-only; formal output was the only writable mount. All containers used `--pull=never --platform linux/amd64 --network none --read-only` with a bounded tmpfs. Frozen source files matched `SOURCE_HASHES.json` before batch 0. Fixture SHA-256: `5531e1296e31064da7661138f6ae9036e473b5c953ebd82b3f1ce28a9409fd61`.

Observed runtime: Docker Desktop local engine 29.8.0, image `python:3.13.5-slim-bookworm`, image ID `sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419`, linux/amd64, Python 3.13.5, kernel `6.6.114.1-microsoft-standard-WSL2`, glibc 2.36. The frozen `ENVIRONMENT.json` instead records Docker unavailable and Linux kernel 6.18.44/glibc 2.41. This is an execution-environment deviation; it was not silently edited. The temporal arithmetic uses fixture X-server ticks, not host clocks. Results are therefore reported against the actual Docker environment, without claiming bit-identical environmental replication.

The candidate fixture bytes are frozen and hash-bound in this branch. The historical #4220 archive available in its branch does not match the archive digest stated in its capsule, and #4433's published branch history does not contain the lossless archive parts. Thus the fixture hash is verified, but its byte-for-byte identity against those predecessor raw archives could not be independently reconciled here. No predecessor result or archive was altered or substituted.

`ARTIFACT_MANIFEST.json` records byte lengths and SHA-256 for every other file in this directory. Raw batch ledgers, outer exit receipts/logs, environment record, raw audit and all ten mutation-control outcomes are retained unchanged.

## Next action

Do not rerun or repair this consumed allocation. A separately named successor should first add and test an auditor check for candidate subprocess return codes against copies of this retained evidence, and should resolve the predecessor-fixture provenance/environment questions before any new formal allocation. Preserve this HOLD and its raw artifacts unchanged.
