# Receipt compaction cost: bytes saved versus processing added

Issue #4395; parent #3544. **PASS_RECEIPT_COMPACTION_COST_CHARACTERIZATION**.
No new runtime, selector, default, model call or GUI action is introduced.
A characterization PASS is not a speedup or product PASS.

## Source and allocation

Base `4c701cc51b06296268ad8d9ae3eff1dd6f2d379d`.
Public source commit `99b965653a9bb365a3a6813cc4ec584bfb00c682` and exact
21-file subtree readback preceded measurement. Freeze SHA256
`d2ab58ee5d163ff4694c294ce1ef8ecc89b6399ec250663b528397f3b146d207`.
Six fresh condition workers each executed once:378 measured calls plus36
excluded warmups. Six worker and six enclosing runner exits0, no timeout,
retry, sample exclusion, replacement or postfreeze scientific change.

Complete unchanged review/receipt/reference functions execute in an isolated
package, not the full CLI/MCP/backend. Six synthetic NO-IMAGE reports are used.
Their failed releases, partial effects and task statuses are test data, not
observed physical input or actual task outcomes. Existing #4350 diagnostic
fidelity work, old APNG work and all foreign sources remain untouched.

## H / T / D / C / U

H: exact reference compaction can reduce JSON bytes while adding processing.
The existing size fallback must preserve information; it does not minimize
latency. T: six shapes,three modes,two warmup and21 measured rotating triplets
per condition. D: full source/exit/414-call accounting, independent exact
reconstruction, unchanged non-receipt outcomes, nonincreasing selected receipt
bytes, stable output hashes and10 effective evidence mutations rejected.
C: canonical uncompressed JSON and a declared consumer normalization boundary;
reference-shaped literals must remain literal. U: actual hosts, transport
compression/queueing, model tokens/viewing, images, cold starts, memory,
concurrency and task benefit are not measured. No calibrated combined standard
uncertainty or coverage factor is estimated. See the frozen PLAN.md.

## Measurement boundary and environment

Linux6.18.44/x86_64, CPython3.13.5, guest AMD EPYC9V74, logical CPU0 affinity,
batch1. Frequency snapshot2596.146MHz is NOT a fixed clock; host load and
physical-core exclusivity are uncontrolled. No Docker/OrbStack image attestation.
Producer timing includes review_bytes plus complete canonical JSON serialization.
Consumer timing includes JSON parse plus the existing expand_receipt API,
including its v1 deepcopy. Imports, fixture creation, file writes, hash checking
and offline verification are outside timing. No network/model/GUI is timed.

Values below are median [minimum,maximum] in milliseconds,21 technical
repetitions per row in one condition worker. Bytes are full UTF-8 JSON envelopes,
not tokens. Total is producer plus consumer for each paired call. All18 rows,
producer/consumer wall and CPU endpoints, and every sample are in retained
AUDIT.json and formal/case-*/case.json after restoration.

|Condition|Mode|Envelope bytes|Total processing ms|
|---|---|---:|---:|
|minimal|plain|1422|0.061522 [0.056996,0.068122]|
|minimal|report_refs|1416|0.159229 [0.151007,0.216976]|
|detail_8192|plain|18130|0.147341 [0.135934,0.274723]|
|detail_8192|report_refs|9784|0.371839 [0.348012,0.479109]|
|repeat_64|plain|84332|1.203035 [1.165429,1.268323]|
|repeat_64|compact|46624|2.295424 [2.261193,2.645419]|
|repeat_64|report_refs|46624|2.604108 [2.485499,3.410628]|
|unique_64|plain|169295|2.510117 [2.413272,2.866761]|
|unique_64|compact|169295|5.196920 [4.967546,5.610801]|
|unique_64|report_refs|169295|5.529679 [5.395818,5.922499]|

The omitted highlight rows are NOT excluded samples: detail_256 and repeat_8,
and all three modes, remain in complete raw data and audit statistics.
Minimal report_refs saves only6 bytes. unique_64 saves none under either option:
falling back avoids wire expansion, not work already spent on candidates.
For repeat_64, report_refs produces the same event-reference bytes as compact,
with additional processing. Do not equate enabling more formats with improvement.

## Conditional transfer calculation

|Quantity|Meaning|Unit|Definition/domain|Type|
|---|---|---|---|---|
|saved_bytes|Encoded envelope reduction|byte (8bits,non-SI)|Plain minus chosen length;positive for crossover|Integer scalar|
|added_seconds|Extra processing time|s|Median paired producer-plus-consumer difference,ns divided by1e9;positive for crossover|Real scalar|
|rate|Effective uncompressed throughput|byte/s|Positive assumed serial link rate|Real scalar|
|crossover_rate|Equal-cost throughput|byte/s|saved_bytes divided by added_seconds|Positive real scalar|

With otherwise identical additive stages, the transfer time of saved bytes must
exceed added processing. Transfer time is saved_bytes divided by rate. Solving
for positive rate gives a benefit only below crossover_rate. Unit check:
byte/(byte/s) is seconds; byte/second is the crossover unit. This is conditional
reasoning, not a measured network or task endpoint; it excludes compression,
overlap, queueing, rendering and model costs.

Minimal report_refs:6B/97215ns -> about61719B/s. detail_8192 report_refs:
8346B/216135ns -> about38.615MB/s. repeat_64 compact:37708B/1103005ns -> about
34.187MB/s. MB is decimal. These paired extra-time medians differ from
subtracting separate total medians. No default route is selected from them.

## Audit, preservation and reproduction

The raw auditor imports no runtime/worker/candidate module and reconstructs
v1 views independently. First audit errors=[]. Ten effective copied-evidence
controls reject, including rehashed semantic changes. Same-author separate
implementation is not independent human review. Six prefreeze unit methods
passed. One source transcription mismatch was caught and corrected before any
import/measurement; CONSTRUCTION.json retains its original identity and reason.
The container tool emitted a terminal-reset/TERM notice after shell output;
worker and saved runner stderr are empty, their actual exits0.

All73 raw/process/result/sidecar files,2026723 member bytes, are retained in six
lossless binary fragments. Archive23980B, SHA256
`f5229225c28164fba5318c902589680fb829be0a8806c4f443c06d329e0ab064`.
The21 readable frozen files plus these73 restore94 exact files. No outcomes are
regenerated instead of retaining them. Fresh restoration reproduces original
AUDIT and CONTROLS stdout byte-for-byte without measurement workers.

From this directory, with CPython3.13 standard library:
```
python -S -B verify.py
python -S -B -m unittest -v test_delivery
```
The restorer requires a new trusted destination, validates relative names,
source/member/part hashes and decoded bounds. It is not a general hostile-path
sandbox. Packaging tests include roundtrip,overwrite refusal and8 corruptions.
Do not invoke consumed measurement IDs. Publication/main/CI states are recorded
in the PR separately; local verification is not remote CI.

## Integration decision

Deliver cost evidence only. Existing opt-in behavior remains unchanged. Validate
actual receipt distributions, host representation and transport/model costs
before any routing/default decision. Related disciplines are information
representation, performance engineering and human-agent interaction. Parent
#3544/#57/#2789 and the global ROADMAP remain open.
