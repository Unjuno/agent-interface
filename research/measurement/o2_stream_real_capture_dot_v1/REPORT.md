# Streaming O2 on retained application captures

## Result

**PASS_RETAINED_CAPTURE_WIRE_PARITY** and **PASS_RETAINED_CAPTURE_ALLOCATION_BENEFIT**, scoped to the frozen offline corpus and this execution.

- Exactly one formal launch;144 encoder calls:108 uninstrumented timing calls and36 separately allocation-instrumented calls
- 18 observations from three previously recorded real application sessions: Calc9, Inkscape5, xterm4
- 15 consecutive transitions:12 changed and3 unchanged;3 initial full frames
- All baseline/candidate wire bytes, decoded RGB, metadata, pre-call state and post-call state agree
- Changed-transition median paired traced-peak ratio: **0.6671454257**, about33.3% lower
- Every observation stayed within the preregistered candidate <=1.20×baseline+32768-byte allocation envelope
- Independent raw audit:2119 checks, zero errors;14/14 effective evidence/gate controls passed
- Child exit0, no timeout, retries, replacements, excluded formal rows, source changes or tuning

All12 changed transitions selected the **tiles** route in both arms. This is new evidence beyond the predecessor's synthetic dense cases, which ultimately selected FULL: savings occur on actually selected tile packets from retained application screenshots too. It remains offline characterization, not fresh GUI or end-to-end evidence.

## Method and provenance

Issue: https://github.com/Unjuno/agent-interface/issues/4362

The exact public StreamingEncoder blob ffb66b14e42d5a09ba894fee244e53d984410237 was materialized from commit6a9386aad7ce7d19c901099e3030473d6612feb2. Current-main canonical encoder0de27f79e6cbf5ded545430b26a87dcacc142b71 and Frame d2629bc94d40cc0a8e1bf9e053585549218629ed match their predecessor identities. No encoder implementation was changed.

Main/source/input pin:6af2b750e37979de585d5a2e3c3d8e0c26926359. All28 original source/provenance/input Git blobs match. PROVENANCE.json retains exact repository paths/refs/URLs/blob identities. Inputs are every recorded observation in research/observation_tiles/results/dogfood-calc-01, dogfood-inkscape-02 and dogfood-xterm-03; no outcome-based selection. Seventeen byte-exact PNG files represent18 observations, including genuine reuse of xterm001. All are1280×800 RGB. Original captured timestamps, action labels and context are retained as historical metadata. Source snapshots were visually checked, but no historical task effect or current authority was inferred.

Each app starts fresh canonical/streaming states in each of four passes. The first three passes measure wall/process CPU without tracemalloc; the fourth measures temporary traced allocations. First-arm order alternates by pass and observation. There are no discarded warmups. PNG decode/imports/preloaded source frames/garbage collection/hashing/output writes are outside the encode measurement. The same default O2 strategy,64-pixel tiles and exact zlib settings apply. The bottom32-pixel edge and ordinary noncontiguous tile windows arise naturally from these original frames; no invented motion/color/geometry was added.

The independent auditor imports neither encoder nor runner. It reconstructs first-pass packets with struct/json/zlib and byte-row copies, compares to original decoded PNG bytes, independently counts dirty tiles, checks every later sample hash, state and original metadata, and recomputes decisions. All36 first-pass wire packets and144 raw measurement rows are retained.

## Allocation detail

| Source | Changed transitions | Median paired traced-peak ratio | Range |
|---|---:|---:|---:|
| Calc |7|0.680987|0.209491–1.000000|
| Inkscape |3|0.379141|0.290064–0.484967|
| xterm |2|0.870965|0.843222–0.898708|

The12 changed transitions touched2–72 of260 possible tiles. The largest saving was Calc observation9:2,033,864→426,077 traced bytes. Calc observation8 was unchanged in peak allocation:631,185 bytes for both encoders. Initial-full and exact-repeat cases were effectively equal. The result therefore supports a corpus-level temporary-allocation benefit, not uniform savings on every request.

These are **tracemalloc-tracked temporary allocations**, not whole-process peak RSS, native allocator consumption or a system-wide memory bound. Source images were preloaded before the brackets.

## Timing and environment

Median of54 paired uninstrumented wall-time ratios was1.03245. There is no demonstrated speedup, calibrated uncertainty or population inference. Three passes over the same small corpus are diagnostic repetition, not independent task replications. Host load, caching and frequency are uncontrolled.23 of144 CPU-delta readings were zero; coarse short-call clock behavior is disclosed and no zero-work inference is made.

Formal supervisor elapsed:2.637 seconds. Execution was limited to one logical CPU,256MiB process address space and30-second CPU/wall ceilings; recorded resource/thread/command/exit/log receipts pass the auditor. No Docker/OrbStack image attestation is claimed. Supplied Linux6.18.44 x86_64, CPython3.12.14, NumPy2.3.5, Pillow12.3.0, zlib1.3.2. Detailed package-version inventory was collected read-only after the run and is explicitly labelled ENVIRONMENT_POSTRUN.json; no software was installed or changed.

## Freeze, audit and control identities

Preformal FREEZE.json SHA256: dbd6c764473f37b599220ba043012263c704eaadaaa5a9d6ed64a94976b0c127,193 bound files. All still match after execution.

- formal-01/samples.jsonl: feefe8575580ac828cb965bb3fbe6b345521fc1a38ac936f29b32bcaab79580e
- formal-01.audit.json:7cfc9e5a90e92f2efc4f8a61114476c8d5a4a0e476b1c0150e43c53723c55c00
- formal-01.controls.json:9cc41652dc9a39e43987c99bb3a8426f13b227d2ed46fb10ef1559d6292a1e9a
- formal-01.launch.json:3434750b2562f136984e10d2c4033398d1882d60175a04e4c97cb66914e369c8

Controls independently reject missing/order/state/input/wire/dirty-count defects and invalid measurement/process/resource/log evidence. An explicitly synthetic measurement-only positive control keeps all wire/state data unchanged and gives allocation PASS; one coherent candidate-peak increase gives allocation HOLD while parity remains PASS. Synthetic control numbers never enter the experimental result. Earlier ineffective control/auditor assumptions and all excluded construction records are preserved in CONSTRUCTION.md and versioned retained files.

## Scope and delivery

The original #4362 synthetic allocation remains consumed and untouched. This is a distinct retained-capture transfer, no model/provider/GPU/paid service, no live GUI/input, no runtime change, and no experimental network or GitHub Actions jobs. The canonical source and previous evidence are unchanged. Independent protocol review and independent read-only result review both approved the scoped result; neither is an external human audit.

No claims are made for current screenshot truth, live acquisition cost, task completion, model benefit/tokens, arbitrary color modes, transport latency, general workload prevalence, hard-real-time behavior, RSS, or production adoption. The reasonable next research boundary is a separately authorized live-path/end-to-end assessment if temporary allocation matters there; this study does not itself authorize integration or another run.

Formal science is complete; do not re-execute launch.py formal-01. Read-only audit commands are python -B audit.py formal-01 and python -B controls.py formal-01. The frozen auditor intentionally binds original process location/interpreter; relocation requires a separately disclosed portable audit wrapper, not altering this first result. Repository publication and repository review remain pending.
