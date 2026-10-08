# Issue #4666 — first paired localization rung

## Disposition: `HOLD_NO_PREREGISTERED_GAIN`

The frozen 12-pair allocation completed once. Independent audit found no
integrity errors, but the predeclared positive gate was not met. This is a
scoped negative/hold result, not an Agent Interface performance result.

## H / T / D / C / U

**H — hypothesis.** With v0 target-stage geometry, task wording, local model,
and decoding held fixed, a foreground 80-pixel coordinate grid with numeric
axis labels (GRID80) lowers center error versus the same unmodified raster
(RAW), without reducing exact target selection or points that hit the target in
the Arena engine.

**T — trial.** Allocation
`arena-v0-target-grid-4666-v1-20260927-01`; seeds 8866601–8866612, difficulty
0.35; one stateless RAW and one GRID80 `/api/generate` call per seed with
counterbalanced order (24 formal calls), plus one excluded RAW warmup. Local
Ollama `qwen2.5vl:7b` digest
`5ced39dfa4bac325dc183dd1e4febaa1c46b3ea28bce48896c8e69c1e79611cc`; pinned
runner/auditor image
`python@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`
(`linux/arm64`). Formal runner used Docker bridge to reach the host-local
Ollama endpoint; this is not a network-egress-isolation claim. No GUI input or
action was sent. Exact prompts, requests, complete responses, images, per-call
timings, truth, and request/image hashes are in `formal/001/`.

**D — decision rule and result.** `PASS_GRID80_LOCALIZATION_SIGNAL_SCOPED`
required all 12 valid pairs; GRID80 exact-target and Engine-hit counts at least
RAW; pooled median center error at most 80% of RAW; and GRID80 lower error in
at least 8/12 pairs.

| Measure | RAW | GRID80 | Gate |
|---|---:|---:|---|
| Valid pairs | 12/12 | 12/12 | pass |
| Exact color+shape target | 12/12 | 12/12 | pass (equal) |
| Engine target hit | 0/12 | 0/12 | pass only as non-decrease; no successful points |
| Median center error | 312.170 px | 265.994 px | 14.79% lower; fails 20% requirement |
| Pairwise lower-error wins | — | 8/12 | pass |
| Mean model wall time | 5.521 s | 5.540 s | descriptive only |

The GRID80/RAW median ratio is 0.8521; the required maximum was 0.80. Therefore
the result is `HOLD_NO_PREREGISTERED_GAIN`, not PASS. Both arms identified the
requested color/shape in every pair, yet neither produced an in-shape target
point in any pair. The point proposals were often outside the 640×480 source
image; out-of-frame proposals remain visible in the retained raw call records.
No threshold or seed was changed after seeing the formal outcomes.

The excluded construction pair (seed 8866600) is separately retained under
`construction/seed-8866600/` and is not included in these counts or medians.
Its two proposals also missed the target. A preformal visual QA revision made
axis glyphs 2× larger; a preformal scorer correction changed even-sample
medians to the standard midpoint average. Both predecessor freezes and the
construction outputs remain available in branch history. No formal calls were
made under the predecessor freezes.

**C — controls and confounds.** Pair arms share v0-generated objects, task
wording, prompt, model digest, decoding, and coordinate mapping; only the
foreground grid/ticks/labels differ. Arm order alternates by seed. The images
are deterministic rasterizations, not Tk/X11 screenshots; target motion,
timing, motor action, and task completion are absent. Requests were sequential
on one host/model, so residual backend load/order effects remain possible.

**U — scope.** One local model digest, one host, twelve seeds, one public v0
generator family and static target stage. This does not establish a real-time
failure frontier, full B0/C1 task effect, held-out composition performance,
cross-domain transfer, or general Agent Interface benefit. `HOLD` means only
that this registered first rung failed its specified positive-signal gate.

## Provenance and verification

- Active source/freeze commit: `aee59a5ff8f3dc6547ac2739dbaf54e50e954e11`.
- Active `FREEZE.json` SHA-256:
  `198c2e294b1c1442a568afa135af672fa9705a510aceda8351a43628a0227275`.
- Formal runner: Docker `--network bridge`, read-only root, all capabilities
  dropped, no-new-privileges, non-root UID 501; output persisted to `formal/001/`.
- Independent audit: separate pinned Docker invocation with `--network none`,
  read-only source and evidence mounts; `audit/AUDIT.json` reports the
  disposition, all 12 pair scores, zero integrity errors, and 8 pairwise wins.
- Run state: `CAPTURED`, 24/24 formal calls, warmup parse valid; no retry.
- Local host suite: 11/11 PASS. Pinned read-only, network-disabled container
  suite: 11/11 PASS. `py_compile` and `git diff --check` PASS.

The CI suite validates the runner/scorer mechanics only. The model result above
is the experiment; the two must not be conflated.
