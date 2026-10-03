# Issue #59 — color-aware independent HUD reader, A01

Owner: Codex thread `01a0b98b-5ce3-7f53-82f3-e09294f24d57`.
Branch: `research/59-hud-ocr-5ce3-20261003`.
Intake main: `38518811f537a5dc3dea3b231036b9006b25d8aa`.

## H / T / D / C / U

- **H:** Red intensity or red chroma contrast can improve generic OCR agreement
  with the retained MAP01 health reader relative to grayscale. The prior
  14-frame pilot suggests the luminance threshold loses red HUD glyphs.
- **T:** Preserve the old post-hoc package. In a new private OrbStack VM/Docker
  engine, run a 14-frame calibration over fixed grayscale, inverted red, and
  inverted red-excess transforms, using fixed Tesseract PSM 8 and 10x nearest
  resampling. Select the most exact-agreeing color transform; tie order is red,
  then red-excess. Freeze that selection before one evaluation of all 204
  remaining observation rows. Evaluate grayscale and the selected color
  transform on identical crops with the same image and engine. Candidate gets
  only opaque IDs, image bytes, and hashes. A separate saved-output auditor
  receives the source events/images and concealed row-to-source mapping.
- **D:** Report exact agreement, blank output, and nonempty wrong output for
  every arm. The proposed finite reader-eligibility gate requires at least 95%
  exact agreement, at most 1% nonempty wrong output, and at least 25 percentage
  points improvement over grayscale on the 204 evaluation rows. Any failed
  condition yields `FAIL_FINITE_REFERENCE_AGREEMENT_GATE`; source/matrix or
  runtime failures yield STOP. This gate is frozen before calibration, and
  calibration selection is frozen before evaluation.
- **C:** Reference health is the retained WAD-specific typed extractor, not
  independently labeled ground truth. All rows are from one previously viewed
  episode; adjacent/duplicate values are correlated. The 204 frame rows are
  disjoint from the 14 calibration rows but are not held-out episodes. Container
  Tesseract/Pillow versions can differ from the original macOS 5.5.2 pilot.
- **U:** A scoped image-reader agreement experiment. It does not identify
  independent useful-feedback onset, threat cause, per-key actuation/release,
  recovery efficacy, matched control benefit, model strategy, or MAP01 exit.
  #59's separately gated live allocation remains unchanged.

## Frozen method

Input source is the immutable v39 runtime from base
`e5270c7bfe50911225afc6c3b5273021331b2bb1`; events SHA-256
`2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381`.
For every typed row, the paired observation names its actual PNG, including
sequence 151's reuse of `150.png`. Verify source RGB hashes before cropping.
Crop box is `(423,591,501,629)`, unchanged from the pilot. Color transforms:

1. `gray`: Pillow luminance conversion.
2. `red`: invert the red channel.
3. `red_excess`: invert `max(0, R - max(G,B))`.

All crops scale 10x using nearest-neighbor. OCR command is Tesseract PSM 8 with
whitelist `0123456789%`; normalization concatenates ASCII digits, preserving
leading zeros. No template/font/WAD lookup enters the candidate.

Calibration rows are the 14 source health-transition rows
37/62/76/81/90/97/103/115/144/154/167/193/200/218. Evaluation rows are the other
204 typed observation rows. Inputs are lossless crops with opaque IDs, shuffled
with seed 59031003. Concealed truth is mounted only in the separate auditor.

## Runtime and stopping boundary

Fresh machine `research-59-hud-ocr-5ce3-20261003` owns its Docker daemon; the shared
OrbStack engine and other machines are outside this study. Initial isolated-mode
build failed at device-cgroup BPF setup before OCR, and that first record is
preserved. Before any scientific execution the owned machine is changed to
normal mode, retaining the private engine and limited Docker mounts. This
environment repair follows the matching [OrbStack report](https://github.com/orbstack/orbstack/issues/2429).
OrbStack machines share a Linux kernel; normal-mode integration is not a separate
security boundary. Setup downloads Docker and image dependencies. Before OCR,
freeze exact image ID, base digest,
package versions, source/input hashes, and resource observations. Candidate and
auditor containers use `--pull=never --network=none --read-only`, 1 CPU, 512 MiB,
no swap, 64 PIDs, read-only input/code and distinct writable outputs. Record
actual cgroup files and Docker inspect, then verify terminal containers and
stop only this owned VM after closeout. No GPU, live game/model/GUI/input occurs.

Each calibration/evaluation candidate runs at most once; auditor runs after
candidate exit 0. No scientific reruns. Exclusive-create files preserve first
outcomes. Unrelated main updates do not change the fixed archived dataset;
any source/input/image drift stops this study. Build/setup STOPs are retained.
