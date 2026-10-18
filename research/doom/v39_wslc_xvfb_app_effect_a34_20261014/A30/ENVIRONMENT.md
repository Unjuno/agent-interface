# Environment and runtime identity

- Windows host date: 2026-10-14; WSLc CLI: 3.0.3.0.
- WSL CLI reports WSL version 2.7.13.0; the application under test is Xvfb in an isolated WSLc container, not WSLg or the physical desktop.
- Frozen local image: `a09-owner-close-xvfb:20261012`, ID `sha256:d3e433793e1b6a0bc9fb821b0aa2648945aaf7ba91c3ecc4b8b74b5123d76592`, amd64 Linux, CPython 3.14.8. It is already present locally; WSLc `--pull never` prevents a registry pull.
- Xvfb, `xkbcomp`, and Python-Xlib are provided by the previously materialized read-only runtime closure at `D:\codex-research\v39-xvfb-a09-env-20261012`. Its package hashes are enumerated below and compared with the A13 runtime record before execution.
- Input source snapshot comes from main commit `014bd4279a716d376f167e14fadc418f57e558f7`. Source is mounted read-only at `/study/SOURCE`; the unique output subdirectory is mounted below `/study/OUTPUT`.
- WSLc requested 1 CPU and 1 GiB RAM, no GPU, network none. In the setup mount smoke WSLc warned: “Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.” Therefore no hard memory-plus-swap ceiling is claimed.
- No package installation, image build, image pull, model call, external network access, or game launch is part of A30.

## Runtime packages

The package SHA-256 values and relevant runtime-file hashes are recorded in `FREEZE.json` and `SHA256SUMS.txt`. The runtime directory remains outside the repository; its original package files are not modified.

## A30 actual outcome

The one-shot runner stopped before candidate startup because `ip` was missing, `/usr/bin/xkbcomp` already existed, and the image lacked a `user` account. No input was sent. The result is HOLD; see `RESULT.md` and `output/A30/HOLD.json`. The container was removed automatically.
