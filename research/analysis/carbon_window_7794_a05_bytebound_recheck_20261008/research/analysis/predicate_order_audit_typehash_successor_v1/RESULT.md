# Issue #5006 — boolean metadata and artifact-hash boundary

## Disposition

**HOLD_PROVENANCE_OR_RUNTIME for the Issue's formal gate.** A one-shot
container diagnostic produced the expected boundary signals, but it is not a
formal PASS: the execution architecture was `linux/arm64` while the Issue
requires `linux/amd64`, and the newly authored probe/verifier bytes were not
published and read back before execution. The invocation is consumed; it was
not retried. The diagnostic outputs are retained unchanged for review.

This HOLD does not alter #4994's published result or promote its finding to a
general security claim.

## H/T/D/C/U

- **H:** Python equality may let JSON booleans substitute for numeric metadata
  in the retained #4994 auditor; an exact-path SHA-256 verifier should reject
  empty, incomplete, or altered manifests.
- **T:** One bounded OrbStack container invocation used the Issue's pinned
  image digest, Python 3.12.14, no network, read-only root, 1 CPU, 512 MiB,
  32-PID limit, read-only source/input mounts, and a fresh output mount. The
  image resolved on this host to `linux/arm64`; the preregistered target is
  `linux/amd64`. No model, GUI, provider, GPU, or production runtime was used.
- **D:** The unchanged raw SHA matched
  `5f48e0274f9fd800ac26af3dd70bd52171700b32ce159f3cdbe0f28c7ec35e7d`.
  The retained legacy auditor returned `PASS_DRIFT_BOUNDARY_MAPPED` for 336
  rows / 21 distributions. All six frozen boolean substitutions remained
  accepted by that legacy auditor; the distinct recursive type-shape gate
  rejected all six. The independently launched manifest verifier accepted
  the complete manifest and rejected all three controls (empty maps, omitted
  path, changed digest). These are diagnostic observations under the actual
  arm64 run, not the Issue's formal decision.
- **C:** Mutations were applied only to deep copies in memory. The predecessor
  ZIP, raw, auditor, and merged result were not edited. The verifier ran as
  separate subprocesses and did not import the candidate type checker.
- **U:** One retained synthetic corpus and one local arm64 host/image. This
  does not establish broad JSON interoperability, general security, runtime
  authority, GUI/task effects, latency, or production behavior.

## Inputs and source identity

- Intake main at Issue creation: `817333806ec0086440fc041a3e3bd5a64a296a1f`
  (as recorded in #5006).
- Evidence branch base at execution: `cdcbf6e8f71e112f50d0c89949bb05f8a61278a6`.
- Baseline auditor blob:
  `1a6cc0e46b32d4cd6989aed118d003cce4cfe399`.
- Frozen archive blob:
  `c38dd2002f201d49b6fc261caff019550a4bf4bc`.
- ZIP SHA-256:
  `81f347c99c7461a210edf98437bd7f8ed298dd6f95070d0da4b447913d11a5c0`.
- Extracted raw SHA-256:
  `5f48e0274f9fd800ac26af3dd70bd52171700b32ce159f3cdbe0f28c7ec35e7d`.
- Extracted predecessor audit SHA-256:
  `55b91ba52c5df69adef809dd1ce721dbb9f59d807dc4c64a83b7cecfa9a1a181`.
- Image:
  `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`;
  required platform linux/amd64, observed platform linux/arm64.
- Newly authored source SHA-256 (computed locally after the run):
  `run_experiment.py` `9e1ce65c17f897ee6f3a628c42d82cfc463ae7812e82cc1c6aa77607c229088a`;
  `verify_manifest.py` `469b80f95756f647940d77127699bf46157ef327e15dd45b593a130f04bc7973`.
  Their post-run publication is intentionally called out as a preregistration
  deviation.

## One-shot command and first outcome

```sh
docker run --rm --name issue5006-audit-typehash-20260928-01 \
  --pull=never --network none --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=16m \
  --cpus 1 --memory 512m --pids-limit 32 \
  --mount type=bind,source=<frozen-src>,target=/src,readonly \
  --mount type=bind,source=<frozen-input>,target=/input,readonly \
  --mount type=bind,source=<fresh-output>,target=/output \
  --workdir /src \
  sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 \
  python3 -B /src/run_experiment.py
```

Exit code: **0**. Captured stdout:

```text
PASS_AUDIT_BOUNDARY_REPAIRED_SCOPED
{"architecture":"aarch64","baseline_distributions":21,"baseline_rows":336,"baseline_status":"PASS_DRIFT_BOUNDARY_MAPPED","bool_mutations_accepted_by_legacy":6,"bool_mutations_rejected_by_strict_type_gate":6,"manifest_negative_controls_rejected":3,"raw_sha256":"5f48e0274f9fd800ac26af3dd70bd52171700b32ce159f3cdbe0f28c7ec35e7d"}
```

The printed candidate status is preserved as raw program output, but the
allocation-level disposition remains HOLD because the frozen environment and
pre-execution source-readback gates were not met. Do not cite the printed PASS
as the Issue's formal PASS.

## Retained files

- `input/RAW_AND_AUDIT.zip`: original lossless predecessor bundle.
- `src/baseline_audit.py`: byte-identical main auditor at the recorded blob.
- `src/run_experiment.py`, `src/verify_manifest.py`: executed diagnostic
  sources, retained after the run without retroactive freeze claims.
- `output/`: raw auditor summary, six mutation outcomes, exact-path manifest,
  manifest negative controls, execution metadata.

