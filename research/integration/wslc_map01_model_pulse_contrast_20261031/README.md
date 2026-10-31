# WSLc MAP01: controlled attack pulse after model grounding

This preregistered pair follows [the full/crop passive-observation probe](../wslc_map01_model_postaction_observe_20261031/), where both image mode and model-selected attack duration differed. Here both fresh allocations received a full X11 screenshot after the same guarded navigation, held-input cancellation, verified release, fresh review and old-alias refusal. A host `gpt-6.1-sol` low-effort call selected the action and point. If it selected fire and passed the same image/binding checks, the experiment applied a fixed pulse independent of its requested duration; the prompt disclosed that distinction. Each allocation then observed eight passive samples without further input.

| Allocation | Model proposed | Fixed executed pulse | Kills before → immediate → final passive sample |
|---|---|---:|---:|
| `ae01` | fire, 500 ms | 500 ms | 0 → 0 → 0 |
| `ae02` | fire, 500 ms | 1,000 ms | 0 → 1 → 1 |

Both selected nearby points, passed all recorded checks, completed with verified input releases, and ended with empty tested keymaps. Both host closes succeeded. Each call reported 12,499 input tokens and 54 output tokens; call durations were 3.501 and 3.087 seconds, respectively, with zero cached input tokens. These call times are not a controlled speed comparison.

This is one sequential, fixed-seed, nonrandomized pair. Model calls, one-pixel target differences, inference timing and continuing game trajectories differ, so the result is consistent with a duration effect in this pair but does not isolate it statistically or establish a general threshold. The simulator supplies the kill counter; cancelled input may have a partial effect. The passive window was about 1.37 seconds, so later effects remain unobserved. The externally fixed 1,000 ms pulse in `ae02` must not be represented as the model's chosen duration. This is not MAP01 completion, a broad reliability result, or an efficiency comparison.

`public.zip` retains the preregistered conditions, frozen code and adapter, X11 screenshots, model responses/usage, game samples and guard/owner evidence. Private model protocol and call files remain local and are hash-indexed in `private-hashes.json`. Run `python audit.py` with Pillow to verify hashes, screenshot and coordinate mapping, pixel gates, the requested-versus-executed pulse, release ordering and passive timeline. WSLc used network none, private Xvfb, 1 CPU, 1 GiB and a 150 s watchdog.
