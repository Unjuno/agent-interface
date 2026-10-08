# Container X11 bounded-recovery matched experiment v3

Status: **PASS for container/X11 mechanics; no model or DOOM efficacy claim.**

Immutable repository context observed before publication: `7356970b15406c74bd2b404327f39c2e6b546022` on `main`. The experiment itself is self-contained and was executed in the disposable Linux container before any repository publication.

## Question

Can an explicitly bounded local recovery action bridge a fixed slow-planner wait better than input-free coast while retaining fail-closed stale-authority behavior and verified terminal release?

This is a cross-domain mechanics test, not a gameplay benchmark. The task is a rendered Tk/X11 tracking process under `Xvfb`. A red marker is moved by deterministic exogenous drift and actual X11 Left/Right key events. The controller infers marker position only from X11 pixels. Exact task state is written by the app to a scorer-only stream and is read only after the controller subprocess exits.

## Conditions

Three matched pairs were executed in alternating order. Every arm used:

- 6 fixed decision cycles;
- fixed simulated planner wait: 340 ms per decision;
- identical 85 ms post-planner input-pulse budget;
- identical rendered task, exogenous drift schedule and visual observation path;
- actual XTest key-down/key-up with X synchronization;
- independent app-side key-state logging and scorer sampling;
- a terminal all-input release.

The only arm difference is planner-wait behavior:

- `coast`: no local input while the planner wait is pending;
- `recovery`: the previous planner-authored direction may be reused for at most 240 ms if the current source frame still satisfies its directional guard. Reuse is cancelled if the marker crosses the guard or moves more than the bounded source displacement.

The slow planner itself is deterministic local code plus sleep. Therefore this experiment isolates interface mechanics and must not be described as a model-quality or model-latency result.

## First-result retention and harness failures

Two development generations failed before the retained v3 result:

1. v1 exposed an Xauthority setup failure, then a run-lifetime mismatch. After repair, a two-pair development probe showed the intended mechanism but was not retained as formal evidence because arm decision counts differed.
2. v2 fixed equal decision cycles and app shutdown synchronization, but a six-pair allocation exceeded the available container execution budget after three complete pairs and one additional recovery arm. It is treated as a harness/resource failure, not silently truncated into a formal sample.
3. v3 changed only the preregistered pair count to three so the whole block fits the container execution budget. The decision logic and pass gates were unchanged from v2. V3 then ran once to completion.

## Result

All three matched pairs favored bounded recovery on the predeclared independent safety-band metric.

| Pair | Coast unsafe | Recovery unsafe | Recovery - coast | Recovery center time |
|---|---:|---:|---:|---:|
| 0 | 649.195 ms | 357.167 ms | -292.028 ms | 1236.878 ms |
| 1 | 681.835 ms | 504.310 ms | -177.525 ms | 1040.559 ms |
| 2 | 649.706 ms | 356.820 ms | -292.886 ms | 1119.889 ms |

Paired median recovery-minus-coast unsafe time: **-292.028 ms**.

Median unsafe fraction falls from **0.2326** for coast to **0.1278** for recovery. Median recovery center-region time is **1119.889 ms** versus **0 ms** for coast in this deliberately constructed fixture. Median maximum absolute marker displacement is approximately **0.601** for recovery versus **0.656** for coast.

These values are descriptive for this synthetic fixture. They do not imply the same effect size in DOOM, desktop applications, or a frontier-model loop.

## Safety / stale-authority exposure

Across all six arms:

- terminal app-side key state was empty in 6/6 arms;
- app-side key press/release counts balanced in 6/6 arms;
- stale re-press before the corresponding planner return was 0;
- the pixel decoder's maximum posthoc error against the nearest independent scorer sample was 0.0203 normalized track units, below the frozen 0.03 mechanics gate.

One natural stale-guard event occurred in recovery pair 1. Guard invalidation to the app-observed KeyRelease was **0.309483 ms**. No key-down was reissued before the corresponding planner return.

A single guard event establishes only one local reaction sample, not a latency distribution.

## Isolation boundary

The controller process does not read `score.jsonl` or `input.jsonl` during execution. It uses only X11 screenshots and XTest input. Scorer and app-side key streams are read by the parent only after controller completion. This gives a useful container-level separation but is not an operating-system security proof; the files share the same container namespace.

## Container execution

Environment observed for v3:

- Linux kernel: `6.18.44`, x86_64;
- CPU exposed to container: AMD EPYC 9V74, 5 online CPUs;
- Python: CPython 3.13.5;
- X server: isolated `Xvfb` display per arm, access-control disabled for the ephemeral display plus an explicit empty `XAUTHORITY` file;
- controller: one Python process per arm;
- task/scorer: one independent Tk Python process per arm.

Executed commands:

```text
python3 -m py_compile container_x11_bounded_recovery_v3.py
python3 container_x11_bounded_recovery_v3.py \
  --pairs 3 --decisions 6 --planner-wait 0.34 --cover-budget 0.24 \
  --out /tmp/container-x11-bounded-recovery-v3
```

The script exited 0 with `formal_mechanics_pass=true`.

## Publication-integrity check

The first complete v3 raw result contains controller events, app-observed input events and independent scorer samples. Its uncompressed concatenated JSONL is **236,588 bytes / 1,387 nonempty lines** with SHA-256:

`9037fe0f3393e8cefa50225362ee2caec661a34dc64381cdaabd0b4fd2194cd3`

A first attempt to publish the 46,208-byte gzip+base64 payload as one GitHub connector write was detected after publication as truncated. That artifact was deleted rather than accepted as evidence. The payload was then divided into small ordered parts with a manifest. No raw experimental bytes or scientific result were changed.

For the final retained form:

- the ordered packed base64 stream is 46,208 bytes with SHA-256 `bea4e69eb6bf67ea4f568de95dc548e7240664b1c9a9e3fb5c9f6c02f55a7f5b`;
- each retained part has its own size and SHA-256 in `raw-manifest.json`;
- local Git blob SHA-1 was recomputed from the original experiment bytes for every final part and matched the corresponding GitHub blob SHA for **9/9 parts**;
- `verify_container_x11_raw_v3.py` was compiled and run in the container against the retained layout, reconstructing the same 236,588-byte / 1,387-line JSONL with the original SHA-256.

This post-write verification is part of the evidence chain because a successful connector response alone did not prove the original large artifact was complete.

## H / T / D / C / U

### H — falsifiable hypothesis

Under the fixed rendered tracking fixture and equal slow-planner schedule, bounded recovery reduces independently scored unsafe exposure relative to coast without leaving input held, re-pressing stale authority before planner return, or failing the visual/stale guard.

### T — minimum validation

Run three complete alternating-order matched pairs in isolated Xvfb displays. Every arm must have exactly six decisions. Retain controller events, app-observed key events, independent scorer samples and hashes. At least one recovery guard invalidation must be naturally exposed across the block.

### D — disposition

**PASS for container/X11 mechanics.**

Formal v3 pass requires:

- terminal empty input in every arm;
- balanced app-side key events in every arm;
- zero stale re-press before planner return;
- at least one stale-guard exposure;
- guard-to-app-release below 5 ms for exposed guard samples;
- maximum visual decoder error below 0.03 normalized units;
- recovery unsafe time lower than coast in every matched pair.

All conditions passed.

### C — ways the interpretation can fail

- The tracking dynamics are synthetic and much simpler than DOOM or desktop GUI semantics.
- The recovery policy is a one-dimensional directional reuse rule; model-authored complex guards are untested here.
- The independent scorer uses exact task state unavailable to the controller; this is appropriate for evaluation but not evidence of a deployable scorer.
- Xvfb/XTest delivery does not prove equivalent timing on WSLg, real desktops, Wayland, Windows or macOS.
- One observed stale cancellation is insufficient for a reaction-time distribution.

### U — uncertainty

Dominant remaining uncertainty is transfer: real MAP01 observation noise, long-lived controller integration, release telemetry composition, independent scorer cadence, and whether a previous high-level policy contains a useful bounded recovery action when combat state changes. No confidence interval or general speedup is claimed from three synthetic pairs.

## Architecture implication

This result supports one narrow architectural move: do not make "input-free coast" the only planner-wait fallback. A previous action may remain locally useful if its authority is explicitly bounded by source evidence, duration and a current observable guard, with immediate cancellation and release when the guard fails.

The next high-information step is not another synthetic refinement. Compose this mechanism with the already-retained release telemetry and independent progress-clock work, then execute a separately leased, preregistered live MAP01 coast-vs-recovery allocation. Keep the same safety gates and do not import the synthetic effect size.

## Retained artifacts

- `container_x11_bounded_recovery_v3.py`: complete executable experiment/auditor;
- `results/container-x11-bounded-recovery-v3/summary.json`: formal result and per-stream SHA-256 hashes;
- `results/container-x11-bounded-recovery-v3/raw-manifest.json`: exact part order, part SHA-256 values, packed/raw hashes, sizes and reconstruction command;
- ordered `raw-first-result.part*.b64` files: gzip+base64 packed controller, app-input and scorer rows from the first complete v3 result;
- `verify_container_x11_raw_v3.py`: fail-closed retained-artifact verifier/reconstructor.
