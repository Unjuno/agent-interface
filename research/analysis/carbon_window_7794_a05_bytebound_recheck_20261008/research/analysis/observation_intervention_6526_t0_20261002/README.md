# Issue #6526 — isolated GUI-observer preflight

This additive directory is construction-only. It checks whether a digest-pinned WSLc image can import Tk, create a window on private Xvfb, and capture that private root window with `xwd`. `xvfb-run` must wrap the container command (not be an image entrypoint) so its temporary Xauthority path is inherited by the smoke process. It is not the preregistered observation-intervention experiment and does not run candidate/auditor workloads or make a scientific claim.

## Frozen image base

`Dockerfile` starts from cached `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` and installs the Tk runtime, Xvfb, X authentication, X11 utilities, and `x11-apps` (which provides `xwd`) needed for this smoke. The build records the final image identity and installed package versions separately; mutable APT package resolution is not described as reproducible until that inventory is retained.

## Construction command

From this directory, build with WSLc (no Docker Desktop):

```powershell
wslc build -t unjuno/observation-intervention-6526-preflight:20261002 .
```

Then run the smoke with network disabled, CPU request 0.25, read-only source, and a dedicated output directory on private Xvfb; invoke `xvfb-run -a python -B /src/preflight_smoke.py` as the container command. Do not infer memory enforcement from any requested setting; WSLc reports cgroup/swap limits unsupported. Preserve `preflight.json`, `tk-root.xwd`, stderr/stdout, exit status, WSLc version, image inspect output, and `dpkg-query` inventory. Remove only a container created by this preflight after retaining its receipts; never touch pre-existing containers.

## H / T / D / C / U boundary

- **H:** The frozen WSLc base can support a self-contained Tk fixture, private Xvfb, and pixel capture after installing the declared runtime dependencies.
- **T:** One isolated construction smoke; no app-task policy arms, action sequence, candidate, auditor, or persisted-effect comparison.
- **D:** Construction pass only if Tk opens on a private display, `xwd` yields a nontrivial image, output receipt parses, and all hashes/versions/exit codes are retained. A failure is a construction STOP, not evidence for or against observer backaction.
- **C:** This may still fail due to missing ABI libraries, Xvfb launch wiring, image-build network or WSLc path conversion; a successful smoke says nothing about shared-resource enforcement.
- **U:** It does not establish screenshot treatment fidelity, observation-induced timing/effect changes, accessibility-tree reads, memory limits, or GUI benefit. A fresh frozen allocation is required for the scientific T0.
