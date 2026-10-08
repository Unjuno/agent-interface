# Executed c318-privsep-06 source reconstruction

The executed `runner_v6_direct.py` is retained conversation-side with SHA-256:

`f7e54e9d9f4495ea8d13968cffe182accc84015573213bd77ae965b0b95c78fe`

To avoid treating a manual full-source transcription as authoritative, GitHub retains it losslessly as:

1. exact `runner_v3.py` in this directory (Git blob `5eb727d16a528291823732c2d18b298c097170fc`, SHA-256 `8e88d63e8d3db5bc02decde94b27b3a3e037eafba9917c09444d945557463a1c`), plus
2. `runner_v6_direct.patch` (SHA-256 `cd0d9194bd104c681183ea77fa64a97eb974acfbbba8e66ee66bb67f6a1bea15`).

Applying the retained patch to the exact v3 source was checked locally before publication and reproduces the executed v6 bytes exactly: `cmp` succeeds and reconstructed SHA-256 is `f7e54e9d9f4495ea8d13968cffe182accc84015573213bd77ae965b0b95c78fe`.

The patch changes only:

- adversarial operation from pathname `os.replace` to direct `open(target,'r+b')` write/truncate/fsync;
- post-window setup settle from 0.6 s to 1.5 s after the separately retained c318-05 GUI readiness failure;
- fresh allocation/display labels and order metadata.

No shared runtime source is changed.
