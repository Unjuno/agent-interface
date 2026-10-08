# Formal run 02 — successor S2 allocation

Allocation `LABEL-CONTROL-AMBIGUITY-6038-T0-S2-20261002-01`, Issue #6038. Successor to formal-01's `STOP_CANDIDATE_CONTAINER_ENTRYPOINT`; formal-01 is not retried or overwritten. Frozen base `d7e20a0d25e0c361d1e7cf56fd103f61fb927a2d`. Candidate/auditor/input identities are in `FREEZE_v2.json`.

## Before run

- Reuse the existing OrbStack context only; no unrelated container is inspected or modified during the run.
- Explicit image operand is `python:3.12-alpine` before the `python ...` process argv; `--pull=never` and frozen ID `sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b` (`linux/arm64`).
- Candidate and auditor are separate one-shot containers. The candidate has no oracle mount; the auditor has no candidate-source mount.
- No retries/substitutions. If candidate container or process fails, auditor count remains zero.

## Frozen container commands

```sh
docker --context orbstack run --rm --pull=never --name ai-6038-t0-s2-candidate-20261002-01 \
  --network none --cpus=1 --memory=256m --pids-limit=64 --read-only \
  --cap-drop=ALL --security-opt=no-new-privileges --user 65532:65532 \
  --mount type=bind,src="$PWD/research/analysis/label_control_ambiguity_6038_t0_v1/candidate.py",dst=/src/candidate.py,readonly \
  --mount type=bind,src="$PWD/research/analysis/label_control_ambiguity_6038_t0_v1/fixture.json",dst=/input/fixture.json,readonly \
  python:3.12-alpine python /src/candidate.py /input/fixture.json
```

```sh
docker --context orbstack run --rm --pull=never --name ai-6038-t0-s2-auditor-20261002-01 \
  --network none --cpus=1 --memory=256m --pids-limit=64 --read-only \
  --cap-drop=ALL --security-opt=no-new-privileges --user 65532:65532 \
  --mount type=bind,src="$PWD/research/analysis/label_control_ambiguity_6038_t0_v1/audit.py",dst=/src/audit.py,readonly \
  --mount type=bind,src="$PWD/research/analysis/label_control_ambiguity_6038_t0_v1/fixture.json",dst=/input/fixture.json,readonly \
  --mount type=bind,src="$PWD/research/analysis/label_control_ambiguity_6038_t0_v1/oracle.json",dst=/input/oracle.json,readonly \
  --mount type=bind,src="$PWD/research/analysis/label_control_ambiguity_6038_t0_v1/results/formal-02/candidate.raw.json",dst=/input/candidate.raw.json,readonly \
  python:3.12-alpine python /src/audit.py /input/fixture.json /input/oracle.json /input/candidate.raw.json
```

## Outcome

**`PASS_METHOD_SCOPED`**. Candidate process invocation=1, exit 0; separate auditor invocation=1, exit 0; retries=0. Both used the explicitly pinned `python:3.12-alpine` `linux/arm64` image under the frozen network-off/read-only/resource-bounded settings. Candidate container received no oracle; auditor container received no candidate source. No unrelated container was changed. Exact wall-clock start/end timestamps and transient container IDs were not captured; unique container names are present in the commands above.

- Candidate rows: 10/10; raw SHA-256 `ea9a070e41bdb0469ac2ab92c90d7ceea6d12f8e15820783547663f4d182c0bb`.
- Candidate stderr empty SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; candidate exit file SHA-256 `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`.
- Auditor disposition `PASS_METHOD_SCOPED`; independently reconstructed 10/10 rows and final field states; four frozen mutations rejected. Audit JSON SHA-256 `99ca783bab60488c5f2b8d06a0dcb1a6200c85913d1e0c5880598a4e29fb0274`.
- Auditor stderr empty SHA-256 is the empty-file digest above; auditor exit file SHA-256 is the same as candidate exit file.
- Correct by policy under the independent final-state oracle: nearest geometry 3/10 (seven wrong-field effects); same-scope grouping 5/10 (five wrong-field effects); relation/abstention 10/10 (seven exact effects, three correct abstentions). This is authored-fixture accounting, not an estimated real-world rate.
- Formal-01 remains `STOP_CANDIDATE_CONTAINER_ENTRYPOINT`, with candidate program invocations=0/auditor=0; it is not overwritten or reclassified by S2.

The result supports only method integrity on these ten synthetic records: exact requested-field→final-field scoring, fail-closed behavior on the planted ambiguous/stale records, and rejection of four output mutations. The observed comparison does **not** validate a pixel grouping algorithm because candidate edges were frozen fixture inputs, and it does not establish GUI prevalence, semantic correctness of real accessibility relations, privacy/safety benefit, latency, or product/runtime behavior. Never rerun S2.
