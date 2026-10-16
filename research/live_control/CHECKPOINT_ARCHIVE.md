# Replayable artifact checkpoint evidence

The previous actual Calc run recorded pre-save cell values and a hash but did not
retain the corresponding file. Candidate effect_checkpoint_v2.py remedies this
for new queries: read bounded source bytes, save them under their SHA-256 filename,
then run the existing sampler on those archived bytes. A sample is returned only
with a matching archive/sample digest. Runtime v30/socket v15 use this worker;
v29 and earlier evidence remain unchanged and no old snapshots are reconstructed.

Each sampled result includes archive_path, artifact_sha256, archive_bytes,
archive_source_path, source_sampled_ns and archive_started_ns. These identify the
artifact being parsed and its relation to the original read. They do not prove an
atomic original read, filesystem durability, action causation or whole-task success.
The same-user filesystem can still be changed; this is not authenticated or
tamper-proof storage. The parsed bytes and claimed digest are checked for agreement.

Form inputs retain the 64 KiB source limit. Workbook samples have an 8 MiB input
limit. New archived bytes are limited to 128 MiB per runtime archive; overflow
returns UNKNOWN. Existing matching snapshots are reused, while existing content
that differs from the expected bytes returns UNKNOWN. The archive is not evicted
automatically. Exclusive creation is not fsync or power-loss recovery. An interrupted
partial write may cause later queries to report archive-content mismatch.
Workbook decompression, parsing time, directory scans and disk operations have no
hard execution bound; the input-size limit does not bound decompressed content.

## Evidence

The filesystem test archives an empty workbook, overwrites it with the expected
cells, archives that version, deletes the source, and replays both snapshots.
The original UNKNOWN and later VERIFIED, including actual cell values, reproduce
exactly. Repeated identical snapshots reuse their paths. Missing input, malformed
archive content and oversized form input return UNKNOWN. The corruption control
intentionally changes its own separate archive file; it is not a valid replay
sample. The 128 MiB total-budget rejection and power-loss behavior are untested.

A full scripted Calc run then uses v30/v15 and the unchanged prepared caller v6.
It enters 612/129, reaches the format dialog, samples UNKNOWN, confirms saving,
samples VERIFIED and independently finishes successfully. After runtime cleanup
deletes the original application directory, both snapshots are still present,
their hashes match, and parsing reproduces both original predicates. Twelve exact
frames, the full delivered prefix, two admitted/released programs and runtime
dependency hashes pass. Query/caller/runtime clock identities explicitly agree.

| Snapshot | Bytes | Archive start to parse finish |
|---|---:|---:|
| Before format confirmation: A1/A2 empty | 4770 | 28.454 ms |
| After confirmation: A1=612, A2=129 | 5674 | 29.626 ms |

These intervals exclude later report serialization and delivery. They are wall
durations from one WSL run, not CPU measurements or a controlled overhead
comparison with v29. Archiving has a cost; no speedup or token claim is made.
The new archive candidate has not repeated the slow-verifier/cancellation tests.

Decision: keep the replayable archive candidate optional. Use it when evaluating
new checkpoint correctness, while preserving v29 as the prior measured version.
This closes the evidence-retention gap for these new samples, not the wider
effect-contract, human-tempo or unfamiliar-application goals.

Evidence: probe_checkpoint_archive.py, results/checkpoint-archive-01,
probe_checkpoint_archive_calc.py and results/checkpoint-archive-calc-01, with
source manifests and archived input bytes.
