# Issue #3803 — saved-response classification

**Disposition: `HOLD_AUDITOR_V1_FAILURE`; offline posthoc audit v2 confirms the classifier output.**

## H/T/D/C/U

- **H:** Counting completed `agent_message` items rather than all completed
  items can accept the predecessor's saved response while preserving the
  auxiliary `error` event and exact stream identity.
- **T:** One deterministic saved-stream replay from #2849's retained plain
  preflight, plus four malformed/ambiguous controls, all in OrbStack with
  `--network none`. This did not invoke a model, host broker, IPC, task runtime,
  or GUI.
- **D:** `origin/main` freeze `fab4f62000ecbae168a1d5c336944b91f37d24ce`;
  image ID `sha256:5cc4d237e6af4548147ddfffc35413faf2487fd585f6a0216221f153f61cf073`;
  Docker context `orbstack`, server 29.4.0, linux/arm64. Predecessor event
  SHA-256 `b6db1cc383a4491ca58b54dd1b81acc090588ac518e5f2d09ea98a63aed247a1`;
  schema SHA-256 `0631ab7b7ba0aaf77a4cbdf758a8dbfba557dfb5120a9d5aa789223c97944291`.
- **C:** The classifier CLI returned 0 and retained one assistant message,
  one auxiliary error item, one completed turn with usage, and schema-valid
  JSON. OrbStack control tests passed 6/6. The first registered independent
  auditor returned 1 because it compared the event hash to the wrong output
  file (`process.json` instead of `input-inventory.json`). This audit defect
  is preserved in `evidence/replay-v1/output/audit-v1-failure.json`; the
  classifier replay was not rerun. A separately written, read-only auditor v2
  then checked the exact same raw input and process output and passed 8/8
  checks. That posthoc result supports the classifier mechanics but does not
  erase the registered audit-v1 failure; therefore the preregistered overall
  disposition remains HOLD, not PASS.
- **U:** Preserve #2849's formal `FAIL_RUNNER_EVENT_COUNT_CONTRACT`, this
  bundle's audit-v1 failure, and the posthoc v2 result distinctly. A new live
  preflight requires its own successor Issue and preregistration. No six-task
  allocation or efficiency claim is made.

## Reproduction commands

Control tests (6 passed):

```sh
docker --context orbstack run --rm --network none --read-only --tmpfs /tmp \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -v "$PWD/research/integration/issue_3803_orbstack_event_classifier_v1:/work:ro" \
  -w /work --entrypoint python \
  sha256:5cc4d237e6af4548147ddfffc35413faf2487fd585f6a0216221f153f61cf073 \
  -m pytest -q -p no:cacheprovider test_classify_saved_stream.py
```

Saved-stream replay (exit 0) mounted the repository read-only and only the
additive output directory writable:

```sh
docker --context orbstack run --rm --network none --read-only --tmpfs /tmp \
  -e PYTHONDONTWRITEBYTECODE=1 -v "$PWD:/repo:ro" \
  -v "$PWD/research/integration/issue_3803_orbstack_event_classifier_v1/evidence/replay-v1/output:/out" \
  --entrypoint python sha256:5cc4d237e6af4548147ddfffc35413faf2487fd585f6a0216221f153f61cf073 \
  /repo/research/integration/issue_3803_orbstack_event_classifier_v1/classify_saved_stream.py \
  /repo/research/integration/issue_2849_orbstack_real_model_preflight_v1/evidence/attempts-live-v2/plain/repo/preflight-result/model-call/events.jsonl \
  /repo/research/integration/issue_2849_orbstack_real_model_preflight_v1/evidence/attempts-live-v2/plain/repo/schema.json \
  /out/replay-result
```

The first independent audit returned 1; corrected posthoc audit v2 returned 0
with all 8 checks true. Both audit records are retained. All containers used
`--network none`; no broker or host IPC directory was mounted.

## Scope boundary

This is offline classifier mechanics only. It does not establish live endpoint
compatibility, semantic quality, GUI/task success, six-task acceptance,
reliability, or efficiency. No seed is retried and predecessor evidence is
unchanged.
