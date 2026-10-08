# Image artifact preparation: local latency versus PNG bytes

2026-09-13 JST. This is an offline replay experiment on recorded real desktop
frames, not a fresh GUI task run or a measurement of model latency/tokens.
It addresses a cost seen in actual assistant use: producing the PNG file that
the model-viewing tool opens after the lossless wire receiver has reconstructed
the image. Frozen A1/A2 sources are unchanged.

## Design

`image_artifact.py` provides three experimental policies via compression level
and exact reuse options. `full6` always writes PNG level 6; `reuse6` references
the prior file only when dimensions, mode and every pixel are equal; `reuse1`
uses the same exact rule with PNG level 1. Changed images are always complete
lossless images. This does not test cropping, perceptual compression or token
reduction.

For each episode, load and verify the raw frame digests before timing. Rotate
the order of the three policies by episode index; each gets a fresh sink and
directory. Time frame comparison, file-existence check and PNG writing. Decode
every referenced artifact after the episode/arm's timed publication sequence
and require exact geometry/mode/pixel equality. Keep whole original app/seed
pairs together in 10,000 bootstrap resamples, RNG 424243.

Ordinary filesystem writes are used, without fsync. OS caches can be warm. This
measures local file preparation, not durable storage, image upload, network
transfer, provider preprocessing, model inference or user-perceived completion.
The producer owns its output directory; externally edited existing PNGs are not
part of the cache contract. A missing cached file causes regeneration. Output
name collisions are rejected rather than overwriting earlier evidence.

## Development evidence

Source: A1 revision 3 development traces, 32 episodes and 236 frames. All 708
policy/frame outputs decoded exactly.

| Policy | Total preparation ms | PNG files written | PNG bytes written |
|---|---:|---:|---:|
| full6 | 7,018.28 | 236 | 9,333,402 |
| reuse6 | 5,680.26 | 193 | 7,101,660 |
| reuse1 | 4,874.51 | 193 | 9,605,074 |

Exact reuse reduced preparation time by 19.06% (95% pair-bootstrap CI
11.09–26.92%). Changing level 6 to level 1 on the reuse path reduced it another
14.19% (12.18–16.31%), while increasing PNG disk bytes by about 35.25%.

The unchanged policy scripts were then applied to both recorded A2 fresh
replicates. Those are validation *replays* of previously completed GUI tasks,
not new live trials of this adapter. Per-run source hashes and parameters are
recorded before measurement in each manifest; source snapshots are included.

## Validation replays

| Recorded source | Frames / decoded policy outputs | Exact reuse time reduction | Level 1 vs level 6 reuse time reduction |
|---|---:|---:|---:|
| A2 replicate 1 | 287 / 861 | 10.81% [4.04, 19.66] | 15.89% [13.74, 18.78] |
| A2 replicate 2 | 266 / 798 | 16.59% [8.40, 24.45] | 16.03% [12.37, 19.91] |

Brackets are separate 95% whole-pair bootstrap intervals. All 1,659 validation
artifacts decoded exactly. Level 1 PNG disk bytes increased from 10,751,508 to
14,053,459 in replicate 1 and from 9,556,960 to 12,531,952 in replicate 2.
The time benefit has a real byte tradeoff, not a compression-ratio improvement.

## Actual use after integration

`results/dogfood-png1-04` records an assistant-driven XTerm session using level 1.
The assistant opened the reconstructed initial, typed and submitted images and
chose the commands itself. Independent output evaluation returned `t810101`.
Image preparation took 27.31 ms initially, 16.56 ms after typing and 17.49 ms
after submission. Local action issue to image readiness was 56.39 ms for typing
and 41.25 ms for submission. These are two action observations, not a latency
distribution or an A/B demonstration.

The surrounding terminal tool calls requested `yield_time_ms=1` and reported
approximately 0.264 and 0.267 seconds wall time for the two input calls. That
does not include all model/tool scheduling or prove an immediate streaming
resume. The gap between the two command-received timestamps was about 10.22
seconds, including assistant inspection, reasoning and tool boundaries. Thus
the actual interaction loop is still much slower than the local image-ready
measurement. The next priority is reducing unnecessary agent/tool boundaries
and allowing guarded local progress while feedback arrives; image encoding
alone cannot establish the user's target operating tempo.

## Integration and decision

`dogfood.py` now uses the shared sink and exposes `--png-compress-level`, default
6 to preserve the existing byte/latency tradeoff. Level 1 is available for local
latency experiments; its end-to-end advantage remains to be measured. An
observation separately reports wire reconstruction readiness, PNG readiness,
image preparation time, and stdout emission start. These are local timestamps,
not a claim about when the remote model receives the image.

Example:

```bash
python3 dogfood.py --app xterm --seed 810101 --png-compress-level 1 --out results/my-level1-session
python3 -m unittest -v test_image_artifact.py
```

Reproduction (new output directories required):

```bash
python3 benchmark_image_artifact.py ../observation_gating/results/development-a1r3-final --out results/image-artifact-development-01
python3 benchmark_image_artifact.py results/fresh-a2r2-r1 --out results/image-artifact-replay-01
python3 benchmark_image_artifact.py results/fresh-a2r2-r2 --out results/image-artifact-replay-02
```

Raw manifests, measurement records and PNGs are retained in those directories.
