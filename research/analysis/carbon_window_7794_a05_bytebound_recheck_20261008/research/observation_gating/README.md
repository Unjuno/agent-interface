# Observation Gating

**Status: A1 O0/O1 completed; O1 passes as a scoped research baseline.**

[Result report](REPORT.md): 96/96 tasks per strategy on four real applications,
zero false suppressions, 17.15% same-trace image reduction (95% CI 13.86–20.65%).
Local speedup is unproven; no model calls or token measurements were made. The
report retains two earlier frozen baseline failures and the excluded startup
screen. A2 exact tile delta is the next experiment.

The first implemented experiment is **A1: O0 vs O1 exact unchanged-frame
suppression**. See [the protocol](PROTOCOL.md), [development and rejected
evidence](DEVELOPMENT.md), and the Python harness below. These are research tools,
not a user-facing runtime distribution.

## First-principles question

If an observation contains no new task-relevant information, why should it cross the model boundary?

The goal is to reduce model-visible visual input without intentionally hiding state the agent still needs.

## Baseline ladder

```text
O0  full screenshot after each step
O1  exact unchanged-frame suppression
O2  exact changed-tile mask / spatial delta
O3  relevant-region gating
O4  local VERIFY before model escalation
O5  persistent visual state + ROI delta
O6  deterministic-route observation skip
```

## Hard gate

A candidate is not promoted if task correctness is lower than the paired baseline under the defined test.

## Primary metrics

- model-visible image observations eliminated;
- observed pixels / transmitted visual bytes;
- false-negative gating (relevant change suppressed);
- false-positive gating (irrelevant change escalated);
- action-to-first-useful-feedback latency;
- p50/p95/p99 local processing latency;
- escalation rate to full-frame observation.

Actual image tokens are a later model-in-loop metric. Pixel counts and bytes must not be renamed as tokens.

## Current safety choice

For the lossless first stage, exact frame/tile comparison is preferred over perceptual hashes. Perceptual similarity can miss small but semantically important GUI changes such as a character, cursor state, or compact control.

Approximate/perceptual methods can be tested only behind an uncertainty fallback and against adversarial small-change cases.

## A1 implementation

- [`exact_gate.py`](exact_gate.py): immutable pixel frames, exact O1 comparison,
  per-observation context/timestamps and an ordered receiver that rejects missing
  or stale image bases. O0 always forwards an image. A new stream always starts
  with a full frame.
- [`gui_suite.py`](gui_suite.py): isolated real X11 application sessions, matched
  task scripts, public feedback, separate final oracles, source freeze, sequential
  paired execution and stop-on-failure behavior.
- [`test_exact_gate.py`](test_exact_gate.py): synthetic one-byte changes at every
  channel/edge position, dimensions/mode changes, malformed storage and transport
  gaps/reordering/reconnect. These tests are not GUI benchmark evidence.
- [`analyze.py`](analyze.py): independently reload and audit PNG evidence, check
  paired tasks/input schedules, and compute image counts, pair bootstrap
  intervals and p50/p95/p99 timing summaries.

Gate equality is exact on `(width, height, mode, pixel bytes)`. SHA-256 is used
only to name and verify archived PNGs **after** task timing. Exact comparison,
capture, serialization, public-context and receiver costs are reported separately.

No model is called. `model_visible_observations` means images sent to a local
reconstructing sink at the intended model boundary. It does not count actual
API requests or image tokens. On a suppressed image, the receiver retains its
last exact frame and still receives fresh observation metadata and public state.

## Reproduce on Linux/X11 (including WSL2)

Install Xvfb, Openbox, wmctrl, XTerm, LibreOffice Calc and Inkscape. Provide a
headful Chromium-family binary. Ubuntu's snap wrapper is not required; this
experiment uses the existing Chrome for Testing binary, with the exact version
recorded in each environment file. Install the Python dependencies from
`research/requirements.txt` (or the matching distro packages).

From the repository root:

```sh
python3 -m unittest discover -s research/observation_gating -p 'test_*.py' -v

# Use a new output directory for every invocation. No result is overwritten.
python3 research/observation_gating/gui_suite.py \
  --chromium /absolute/path/to/chrome \
  --strategies O0 --pairs 1 --seed 1101 \
  --out research/observation_gating/results-local/baseline

python3 research/observation_gating/gui_suite.py \
  --chromium /absolute/path/to/chrome --pairs 4 --seed 1301 \
  --out research/observation_gating/results-local/development

python3 research/observation_gating/gui_suite.py \
  --chromium /absolute/path/to/chrome --freeze \
  --out research/observation_gating/results-local/frozen

python3 research/observation_gating/gui_suite.py \
  --chromium /absolute/path/to/chrome --phase fresh \
  --manifest research/observation_gating/results-local/frozen/freeze.json \
  --pairs 12 --seed 490101 \
  --out research/observation_gating/results-local/fresh-r1

# Repeat with seed 590101 and a fresh-r2 output directory, then audit both:
python3 research/observation_gating/analyze.py \
  research/observation_gating/results-local/fresh-r1 \
  research/observation_gating/results-local/fresh-r2 \
  --out research/observation_gating/results-local/summary
```

The published seeds reproduce this experiment. A new tuned candidate needs new
evaluation seeds and a new freeze. An analyzer `efficiency_gate: PASS` alone is
not a promotion: the full protocol's planned sample and correctness requirements
must also be satisfied. Do not analyze or pool a directory containing
`STOPPED.json` as a completed paired result.

## Evidence layout

Each suite saves `environment.json`, `schedule.json`, append-only `runs.jsonl`,
and a `COMPLETE.json` or `STOPPED.json` marker. Each episode saves:

```text
result.json          # success, counts, pixels, oracle, timings and goal
actions.json         # issue, delivery, first receipt, first change, public effect
observations.jsonl   # every captured sample, context and image-base references
frames/<sha256>.png  # all distinct captured frames, losslessly retained
application.txt      # application diagnostics
sheet.xlsx / shape.svg / submitted.txt   # task output, including on failure
```

Success is scored after control ends. The controller receives task inputs and
public observations, not the output path or oracle results. Captured and
forwarded pixels are distinct counters. Setup captures, launch time, fresh
observation receipt and semantic/public completion are also kept separate.

The current receiver assumes reliable ordered in-process transport. A remote
adapter must establish a fresh full-image base after loss/reconnect. This
experiment does not implement such an adapter or establish model-in-loop behavior.
