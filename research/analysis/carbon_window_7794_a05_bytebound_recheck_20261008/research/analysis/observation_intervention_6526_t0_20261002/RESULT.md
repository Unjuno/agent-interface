# Issue #6526 WSLc construction preflight — STOP

## Disposition

`STOP_WSLc_XVFB_RUNTIME_ENVIRONMENT`. This is environment-preflight evidence only. Formal construction checks, candidate, independent auditor, and scientific rows are all **0**. No retry of the GUI smoke is authorized by this record. The observation-intervention hypothesis remains untested; this is neither a scientific PASS nor FAIL.

## Exact attempts

The image was built locally with WSLc (Microsoft WSL Containers CLI 3.0.1.0), not Docker Desktop, from `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`. Debian Trixie package resolution was mutable. Initial image `sha256:57ade377c54650b9053c589dfabb9a96a54bcec0dab72ceb024e1ac2ed144b9c` installed Tk/Xvfb/X11 utilities but omitted `xwd`; its one smoke container did not produce a receipt and was inspected, stopped, and removed. The package omission was directly confirmed (`xwd: not found`).

An additive correction added `x11-apps` and produced image `sha256:bf8ebd7f5574bdc6d74d72dda92254e3099db085d7a387135f5f72bc0d738ed4`. Diagnostic inspection found that a manual child process needed the temporary `XAUTHORITY` from `xvfb-run`; the container was stopped and removed after inspection. A corrected image entrypoint removed `xvfb-run`, with the intent to invoke it as the container command instead. That image, `sha256:644f60ee84c0db8b3d7a65bd722651fcb2568a38e39a2debaca2c90177badd7c`, built successfully, but the single bounded invocation

```text
wslc run --rm --network none --cpus 0.25 --mount type=bind,source=<source>,target=/src,readonly --mount type=bind,source=<output>,target=/out unjuno/observation-intervention-6526-preflight:20261002 xvfb-run -a python -B /src/preflight_smoke.py
```

exited 1 with `_tkinter.TclError: no display name and no $DISPLAY environment variable`. The `--rm` container was confirmed absent after exit. Output directory stayed empty. Image inspect confirms linux/amd64 and the three image IDs above; the final image size is 361,919,202 bytes. No image is pushed to a registry.

## Scope and next gate

The first attempt also exposed a WSLc CLI mismatch: `wslc build` has a boolean `--pull` (no `--pull=false`), and WSLc's documented run interface differs from Docker Desktop expectations. Those were corrected before the final attempt. No memory cap was requested or inferred. The WSL CLI reports 3.0.1.0 while Ubuntu is WSL version 2; no WSL 3 distro is present.

Do not begin the scientific T0 from these images. A future allocation requires a prospectively frozen startup strategy with a verified private-display environment, a clean output location, package inventory, exact captured streams/exit, and independent review before any candidate. Keep this GUI work separate from Issue #6389, whose first native-vs-container migration pilot explicitly excludes GUI and concurrent heavy workloads.
