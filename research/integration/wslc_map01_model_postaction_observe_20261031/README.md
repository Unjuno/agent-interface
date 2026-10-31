# WSLc MAP01: passive observation after model-directed attack

This preregistered pair follows the [earlier full/crop pair](../wslc_map01_model_recovery_crop_full_pair_20261031/), which observed the kill counter only immediately after attack. The fixed order was reversed: full `ad01`, then crop `ad02`. Both fresh allocations used Freedoom2 MAP01 skill 1, seed 991031, the same guarded cancellation/review and stale-alias refusal, and one host `gpt-6.1-sol` low-effort image call. A proposed attack had to pass the same image/binding and input-stage checks. After completion with verified release (or refusal without dispatch), the runner took up to eight passive samples at 150 ms intervals with no further input.

| Image | Model-selected attack | Kills before → immediate → final passive sample | Input tokens (cached) | Call time |
|---|---:|---:|---:|---:|
| Full 1280×1024 | 1,000 ms | 0 → 1 → 1 | 12,476 (8,192) | 3.584 s |
| Crop 640×480 | 500 ms | 0 → 0 → 0 | 11,301 (0) | 3.200 s |

Both actions passed the recorded pixel/binding gates and completed with verified empty releases; both owner closes and final tested keymaps were empty. Eight passive samples were retained in each arm, ending about 1.37 s after the immediate post-action sample. The prior pair's missing delayed observation cannot be reconstructed retrospectively; these are new attempts.

The different model-selected durations, inference times, cache states and continuing simulation time confound attribution. One fixed-seed, nonrandomized pair cannot establish an image-mode effect, statistical performance, general safety, model efficiency advantage or MAP01 completion. The simulator's kill counter is not an independent external observer; cancellation may have had an unknown partial effect. The zero counter only covers the recorded window.

`public.zip` retains conditions, frozen runner/host/adapter, screenshots, model outputs/usage, samples and owner/guard evidence; private protocol/call files remain local and are indexed by `private-hashes.json`. Run `python audit.py` with Pillow to validate hashes, crop and coordinate mapping, visual gates, release ordering and the passive timeline. WSLc had network none, private Xvfb, 1 CPU, 1 GiB and a 150-second watchdog.
