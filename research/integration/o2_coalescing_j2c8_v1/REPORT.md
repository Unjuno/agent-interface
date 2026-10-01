# #4392 — O2 frame-selection composition

## Result

**PASS_O2_COALESCING_COMPOSITION_SCOPED.** One public-source-first allocation, 36 complete cases, 72 producer/consumer processes and six separately observed successful batch exits. Formal retries, replacements, exclusions, pooling and postfreeze source changes: zero. This qualifies only the declared component composition, not the production runtime, actual model benefit or global ROADMAP.

| Per 12 cases | FIFO | ENCODE_THEN_SELECT | SELECT_THEN_ENCODE |
|---|---:|---:|---:|
| Frame encodes, including bootstrap | 52 | 52 | 28 |
| Frame packets delivered | 52 | 28 | 28 |
| Decoder refusals | 0 | 12 | 0 |
| Cases with a refusal | 0 | 10 | 0 |
| Authored critical records delivered | 4 | 4 | 4 |
| Generated frame-wire bytes | 16,600 | 16,600 | 9,916 |
| Delivered frame-wire bytes | 16,600 | 9,976 | 9,916 |

Counters are exact finite observations. Bytes exclude JSON/hex harness envelopes and critical-record transport; they are NOT total transport costs, model tokens or measured speed. FIFO's reducer diagnostic also lists 24 potentially coalescible frames, but FIFO actually omits none. Each selection arm really omits 24 source frames. Pre-encode selection saves 24 calls, including no claim about runtime CPU benefit.

## What happened

The queue's selection IDs are identical in both selection modes. In ENCODE_THEN_SELECT, encoding omitted frames still advances sender sequence and base. The selected packet therefore does not match the receiving decoder's expected consecutive pair. The existing decoder refuses without changing its last accepted pixels or metadata. This is safe refusal with unavailable latest observation, not silent pixel corruption or a codec defect.

In SELECT_THEN_ENCODE, only selected frames advance the codec state. All 28 delivered frames decode with exact selected pixels and original source identity/timestamp. The two scopes in TWO_STREAMS retain separate bases. All four synthetic critical labels in each mode survive with exact source order; that does not recover any omitted intermediate image.

UNCHANGED_BURST and ABA_BURST expose a distinct interpretation problem: a negative-mode decoder can have pixels equal to the final source while still retaining bootstrap observation identity. Pixel equality is not receipt of the latest observation. The pre-encoding approach preserves a transport sequence over selected frames, not continuous capture coverage. Even FIFO only covers the discrete supplied frames.

Delivered packet-kind counts:

| Mode | full | tiles | unchanged |
|---|---:|---:|---:|
| FIFO | 14 | 32 | 6 |
| ENCODE_THEN_SELECT | 14 | 12 | 2 |
| SELECT_THEN_ENCODE | 14 | 10 | 4 |

All full packets here are bootstrap packets. The statement that the decoder would also refuse a full update with the wrong sequence follows from the pinned code and conditional argument, not a separately measured full-update gap in this matrix. Expiry, reconnect and post-selection packet loss were not measured.

## H / T / D / C / U

H: the existing latest-state reducer composes with the existing ordered O2 codec when selection precedes encoding, not when encoded dependency packets are silently omitted.

T: six conditions x three compositions x two fresh repetitions; synthetic 16x12 L frames, 4-pixel tiles; all source bytes/IDs equal across modes; actual separate producer and consumer executions over pipes. Exact unchanged queue, encoder, decoder and Frame modules. See PROTOCOL.md for the complete fixed corpus, variable/unit table, conditional induction, counters and stop rules.

D: all 36 cases, 72 actor and six batch exits, exact source/packet/pixel/metadata/selection joins and the first-outcome gates passed. A separately written stdlib raw-only audit checks 1,499 predicates with errors=[]; ten effective well-formed copied-record controls all reject. Eight unit methods passed before the freeze. Eleven frozen source/plan/environment files remain byte-identical. The audit implementation/process is separate, but the author is the same; this is not independent human review.

C: reliable ordered delivery after encoding, no concurrent mutation, per-scope codecs and a bootstrap are essential. Source frames and event classes are authored synthetic data. No real focus loss, authority change or verified application effect was generated. No application-level backpressure queue or model agent was run. The negative composition is an explicit research comparator, not a claim about how production currently connects these modules.

U: no live freshness-at-display, capture completeness, temporal event detection, automatic resync, source authentication, arbitrary GUI correctness, model quality, latency/CPU/memory/token benefit, distributed or production guarantee. Counts are finite coverage, not failure-rate estimates. Logical source times and real process diagnostic timestamps are never subtracted across clocks. No calibrated combined uncertainty or coverage factor is manufactured.

## Environment and chronology

Provided Linux x86_64 execution container; CPython 3.13.5, NumPy 2.3.5, zlib 1.3.1, guest AMD EPYC 9V74. Docker executable absent; no Docker/OrbStack immutable image identity is asserted. No installation, model/provider, GUI/native input, user document or experiment external-network traffic. GitHub MCP is source/publication transport, not the experimental path. Actor environments contain only explicit locale/path/thread/bytecode settings.

Intake main: 4c701cc51b06296268ad8d9ae3eff1dd6f2d379d.
Public full-source commit: 5369ea4613da9ed3726cef6ffc3f6d759e8fdb19.
Full 12-file source tree: 065c24fc29d5b65d08b36f99f8d1b3a842017ecc.
FREEZE SHA256: 545a3acc47311e0aeffd964ff32809f06961dcd97b9759e5d9c5c1cce1efbad7.
Public readback and Issue comment5841170700 preceded every formal case. First-outcome comment5841184421 preceded packaging. All original sources, plan, raw inputs/outputs, process receipts and construction corrections are retained.

## Preserved preparation correction

Construction v0 ran nine excluded cases. Its original auditor passed, but self-review found two problems: input source IDs included mode, and FIFO incorrectly granted a continuous-coverage label. Before public freeze, both were corrected and the auditor strengthened with equal-source and no-continuous-coverage checks. Old five source files, raw results, old audit and old controls are retained unchanged. Corrected construction_v1 ran nine separate excluded cases, then passed 333 checks, ten effective mutations and eight units. Formal cases were zero throughout correction. The old construction is not retrospectively promoted by the corrected audit.

## Integration decision and remaining roadmap

Retain this as a specific observation-pipeline constraint: run source selection before stateful O2 sequence/base allocation, or explicitly preserve/reestablish a valid decoder chain by a separately tested protocol. Do not renumber arbitrary encoded deltas. Carry original observation IDs and coalesced-history metadata independently of codec sequence. Keep critical event delivery independent, and do not infer missing transient imagery from the latest image.

No shared runtime, workflow, root index or historical result was edited. #43/#57/#2789 and the broader ROADMAP remain open for a real model/task comparison and complete entry-path validation. The earlier p6k2 memory/CPU HOLD remains unchanged and is not republished in this capsule. Research delivery through a PR is not runtime adoption.

For offline review use the retained raw auditor and tests; do not invoke consumed launch.py/run.py allocations. Publication restoration and CI results are separate gates, reported in README/PR rather than inferred here.

ERROR CHECK: 12 refused packets occur in ten cases, not 12 independent failed cases. Authored critical labels are not observed real events. Encode-call/byte differences are not latency or token measurements. Full-update-gap behavior is conditional code reasoning, not an empirical arm. All observed outputs deny continuous visual coverage and task/input authority.
