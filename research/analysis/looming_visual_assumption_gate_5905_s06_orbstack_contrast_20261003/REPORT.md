# Issue #6808 S06 — photometric encoding invariance

## Result

`PASS_METHOD_SCOPED`. The frozen image-only candidate ran once (exit 0) in the
private OrbStack Docker engine; the separate independent raw-only auditor ran
once (exit 0). No retry. The frozen main SHA `49cc67de82ed48980245a6e25376bb3ced700a01`
still matched local HEAD and GitHub `main` after execution.

- 36/36 rows independently reconstructed; 9/9 positive rows produced the
  simulated cue with TTC error within 0.06 s and TTC <= 0.30 s.
- 21/21 visible controls produced no cue; 15 were rejected and the six
  missing-anchor variants returned UNKNOWN. The six latent-cause rows were
  paired into three byte-identical approach/rigid-growth pairs; each pair
  returned identical UNKNOWN for every photometric variant.
- All 12 families preserved the exact threshold-128 masks and candidate
  decision/reason/scale/TTC over native, low-contrast and near-threshold
  encodings. Five of five preregistered corruptions were rejected; false
  SAFE=0; audit errors=0.

This supports only implementation-level invariance on this finite synthetic
PGM fixture with deliberately mask-preserving transforms. It does not test
sensor noise, lossy encoding, ordinary images, GUI/game behavior, a live
controller, actual action/release, latency, safety, task effect or product
benefit. The masks were held constant by construction, so the result must not
be generalized to robustness under arbitrary photometric changes.

## Execution and retained evidence

Allocation, hashes, image, resources and exact commands are in
[`FREEZE.json`](FREEZE.json). Raw candidate output and its exit/log are under
`formal/candidate_output/`; the independent raw-only audit and its exit/log
are under `formal/auditor_output/`. `CANDIDATE_INPUT_SHA256.json` and
`AUDIT_INPUT_SHA256.json` retain per-file manifests. Candidate raw SHA-256 is
`d95526163151e0e814c6923d8c449f33d5d8209987e3cf307cd25d16e6a78d99`; audit
SHA-256 is `5c7dfaf45e68151a845b97aacdc9291d13cd9898318942688470dbf4639c9f65`.

The first local wrapper attempt failed to open a root-owned VM log path before
`docker run` could start. It created no container and did not consume the
candidate invocation. The unchanged frozen Docker command was then run once
with root-owned log collection; the event is retained in
`formal/runner-preflight-permission.log`. The post-run private-engine inventory
was empty.

Construction tests: 3/3. Analysis index: 591 retained result/failure
directories, check passed. These construction/CI checks are separate from the
formal candidate and auditor outcome. Full local CI results are recorded in
`LOCAL_CI.md` after execution.
