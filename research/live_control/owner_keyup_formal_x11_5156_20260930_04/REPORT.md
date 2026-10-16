# Issue #5156 — Allocation 04 execution STOP

**Disposition: `STOP_RUNNER_ENTRYPOINT_BEFORE_XLIB_PREFLIGHT`.** The one
authorized container invocation exited before the Xlib preflight or formal
runner started. This is a launch-command failure, not a scientific FAIL or
PASS. The allocation is consumed; no retry was made.

## H / T / D / C / U

- **H:** Per-key owner-thread XTest KeyRelease-to-XSync intervals can be
  recorded inside the caller's release interval without changing admission or
  release semantics.
- **T:** Allocation `MAP01-OWNER-KEYUP-BRACKET-5156-20260930-04`; one isolated
  offline Xvfb fixture in the assigned image, followed by a separate
  raw-only audit only if the formal runner exits 0.
- **D:** STOP before fixture. Container invocation exit code 2. The image's
  configured entrypoint is `python3`; the invocation supplied `sh -c` without
  overriding that entrypoint, so Python tried to open `/repo/.../sh` as its
  script and exited. The Xlib preflight itself did not run. Formal runner 0,
  raw rows 0, independent audit invocations 0. No retry.
- **C:** The exact assigned pre-existing OrbStack image was present:
  `sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27`,
  `linux/arm64`; network none; read-only source/root; one CPU, 512 MiB, 64
  PIDs. The source freeze was based on `ea61a08a52b4a3b01c5e8f2873433e20a7b77ad1`;
  current main at launch was `bc57d55d4e0a4e75d1945d541ed27fce7cb2b955`. All
  four main-source Git blob/SHA-256 identities and all candidate-file hashes
  were rechecked and matched the retained freeze.
- **U:** No Xlib availability conclusion, Xvfb fixture, XTest request, keymap
  transition, owner-thread interval, GUI input, MAP01/game, model/provider,
  GPU, or task-effect evidence. The frozen scientific hypothesis is undecided.

## Construction and preservation

- Independent candidate auditor controls: 7/7 passed on host CPython 3.14.5.
- The additional host owner integration suite could not import `Xlib`; no host
  dependency was installed or modified.
- Exact failed invocation and image-entrypoint evidence are in
  `results/formal-01/STOP.json`.
- The STOP JSON is not an empty formal result and must not be passed to the
  raw auditor. No raw stream exists; the auditor was correctly not invoked.

## Required successor boundary

Any future attempt requires a new allocation and fresh coordinator assignment.
Its preregistration must explicitly override the image's `python3` entrypoint
for the Xlib/Xvfb command, validate argv with a zero-input smoke gate, and
preserve this consumed STOP unchanged. This record itself grants no retry or
resource lease.
