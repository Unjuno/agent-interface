# A12 frozen pre-run protocol — Issue #5309

Allocation: `5309-EVIDENCE-SEMANTICS-HELDOUT-A12-20261007`
Base: `origin/main` = `9fb2dd6782d1d1477a00d14be870487fd4c54fa2`
Branch: `research/5309-evidence-semantics-a12-20261007`
Container: `node:26-alpine@sha256:0b36e8c136b94cd4fcf02188228e76c31ad5872eef3fec8cbd2eee500cfd9e80`, local image ID `sha256:0b36e8c136b94cd4fcf02188228e76c31ad5872eef3fec8cbd2eee500cfd9e80`, Linux/arm64, Node v26.10.0. Network disabled, root filesystem read-only, 1 CPU, 256 MiB, 64 pids, all capabilities dropped, no-new-privileges. Only explicitly mounted files are visible to each stage.

## H / T / D / C / U

- **H:** With the same already-admissible actions and equal predicted information gain, a fixed witness-aware chooser yields more independently effect-witnessed completions than lexical generic information-gain choice on a held-out non-isomorphic topology, among cases with a correct prediction and an affordable preserving action. For misspecified predictions, completion classification follows realized receipt evidence: a real supported effect may complete; an unsupported hint may not.
- **T:** Exhaustively enumerate 16 states over `cycle3`, `branch_merge4`, `asymmetric4` (seen) and `lollipop5` (held out), crossed with correct/misspecified predicted preserving-action sets, cost budgets 0/1/2, and prior-witness absent/present: 192 cases × 2 arms = 384 rows. Each action has predicted IG=1; candidate-visible costs, budget, safe/admissible set, and predicted preserving actions are identical between arms. Candidate input excludes topology identity, transitions, witness state, oracle, and correctness stratum. Candidate selection, environment effect generation, and raw-only audit run separately; no model or OS input.
- **D:** `PASS_HELDOUT_EFFECT_SEMANTICS_SCOPED` only if all 384 arm rows reconstruct, topology families have distinct frozen degree signatures, choices stay within the shared admitted set and budget, prior-witness cases take no action, every completion is supported by a case/action/destination/effect/source-bound receipt, unsupported completions=0, authority grants=0, and WITNESS_AWARE has a strict completion advantage in held-out/correct/affordable/no-prior cases. Any mismatch is retained as FAIL; no retry. Crucially, there is **no zero-completion requirement for the misspecified stratum**: actual receipt truth, not model-prediction correctness, determines completion.
- **C:** The hand-authored transition family, tie-break, prediction sets, and costs may favor the witness-aware policy; one held-out family is not broad generalization. Mandatory effect readback may make ranking unnecessary in a real system. A model misspecification may accidentally select a truly preserving transition.
- **U:** No learned dynamics, natural GUI state, real receipt producer, app side-effect, temporal freshness/release behavior, calibrated cost/risk, or user utility. The finite result cannot establish safety, latency, human-tempo benefit, or product-level transfer.

## Construction and freeze boundary

The six Node construction tests and deterministic fixture generator ran before this freeze. They validate schema, candidate/oracle separation, equal action-set/IG construction, mutation rejection, and expected gate logic; they are construction evidence, not the formal CLI/container allocation. Container runtime and exact read-only-input/writable-output mount syntax were smoke-tested separately. `FREEZE_SHA256SUMS.txt` binds all formal source, test, input, oracle and protocol bytes. Before execution, require unchanged `origin/main`, all frozen hashes valid, and formal output paths absent. Candidate, environment, and auditor each get exactly one launch attempt; any nonzero/launch failure is retained as STOP/FAIL with no retry.

## Frozen one-shot commands

Run from this allocation directory. The image is addressed by its immutable local image ID, not a mutable tag. The commands mount only stage-specific files; `/out` is the only writable mount.

```bash
IMAGE=sha256:0b36e8c136b94cd4fcf02188228e76c31ad5872eef3fec8cbd2eee500cfd9e80

docker run --rm --name ai5309-a12-candidate-20261007 --network none --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=16m --memory 256m --cpus 1 --pids-limit 64 \
  --cap-drop ALL --security-opt no-new-privileges \
  --mount type=bind,src="$PWD/candidate.mjs",dst=/candidate.mjs,readonly \
  --mount type=bind,src="$PWD/candidate-input.json",dst=/candidate-input.json,readonly \
  --mount type=bind,src="$PWD/out",dst=/out \
  "$IMAGE" node /candidate.mjs /candidate-input.json /out/candidate-choices.json

docker run --rm --name ai5309-a12-environment-20261007 --network none --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=16m --memory 256m --cpus 1 --pids-limit 64 \
  --cap-drop ALL --security-opt no-new-privileges \
  --mount type=bind,src="$PWD/environment.mjs",dst=/environment.mjs,readonly \
  --mount type=bind,src="$PWD/candidate-input.json",dst=/candidate-input.json,readonly \
  --mount type=bind,src="$PWD/oracle.json",dst=/oracle.json,readonly \
  --mount type=bind,src="$PWD/out/candidate-choices.json",dst=/candidate-choices.json,readonly \
  --mount type=bind,src="$PWD/out",dst=/out \
  "$IMAGE" node /environment.mjs /candidate-input.json /candidate-choices.json /oracle.json /out/candidate-raw.json

docker run --rm --name ai5309-a12-auditor-20261007 --network none --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=16m --memory 256m --cpus 1 --pids-limit 64 \
  --cap-drop ALL --security-opt no-new-privileges \
  --mount type=bind,src="$PWD/auditor.mjs",dst=/auditor.mjs,readonly \
  --mount type=bind,src="$PWD/candidate-input.json",dst=/candidate-input.json,readonly \
  --mount type=bind,src="$PWD/oracle.json",dst=/oracle.json,readonly \
  --mount type=bind,src="$PWD/out/candidate-choices.json",dst=/candidate-choices.json,readonly \
  --mount type=bind,src="$PWD/out/candidate-raw.json",dst=/candidate-raw.json,readonly \
  --mount type=bind,src="$PWD/out",dst=/out \
  "$IMAGE" node /auditor.mjs /candidate-input.json /candidate-choices.json /candidate-raw.json /oracle.json /out/audit.json
```

The formal commands are intentionally not wrapped in automatic retry logic. The pre-run checksum manifest covers the protocol and runner arguments; `RUN_RECORD.md` records the exact outcome and post-run checksums.
