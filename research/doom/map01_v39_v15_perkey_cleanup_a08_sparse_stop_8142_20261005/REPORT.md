# A08 result — STOP before test setup completed

A08 invoked the candidate process once, but the sparse worktree contained only `research/doom`; importing the frozen current-main `input_owner_v12.py` failed with `ModuleNotFoundError`. No fake-X owner, executor, key action, or raw candidate result was created. Disposition: `STOP_BEFORE_TREATMENT_SPARSE_SOURCE_OMISSION`.

The shell wrapper also attempted to assign zsh's read-only `status` parameter after the Python process returned; that message is separately retained in `results/shell_wrapper.stderr.txt`. The Python import traceback remains in `results/candidate.stderr.log`. A08 was not rerun. A09 is a distinct one-shot run from the same source SHA after checking out `research/live_control` and `research/observation_tiles` and verifying imports from that checkout.

OrbStack preflight separately failed while reading a cached image blob (`operation not supported`); see `container_probe.txt`. A08 provides no evidence for or against KeyRelease retry. Exact candidate/source pins are in `FREEZE.json` and `source-manifest.json`.
