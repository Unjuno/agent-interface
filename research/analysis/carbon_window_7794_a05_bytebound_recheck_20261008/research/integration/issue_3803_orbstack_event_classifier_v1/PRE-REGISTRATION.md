# Issue #3803 offline saved-response replay

Frozen before the offline container replay. This is a successor to #2849's
retained real-model failure `FAIL_RUNNER_EVENT_COUNT_CONTRACT`; it does not
replace that result.

## H/T/D/C/U

- **H:** Counting only completed `agent_message` items while retaining the
  auxiliary completed `error` item will produce a valid one-message process
  receipt from the exact saved stream, with schema-valid JSON and no new
  external invocation.
- **T:** One deterministic replay of the retained plain-schema response from
  #2849's `issue_2849_orbstack_real_model_preflight_v1` evidence. Run the
  classifier and independent audit in OrbStack containers with `--network
  none`, read-only input mounts, and a pinned image. Also run four synthetic
  classification controls (missing, duplicate assistant, error-only, malformed
  stream) that must refuse.
- **D:** Input event SHA-256:
  `b6db1cc383a4491ca58b54dd1b81acc090588ac518e5f2d09ea98a63aed247a1`.
  Frozen plain schema SHA-256:
  `0631ab7b7ba0aaf77a4cbdf758a8dbfba557dfb5120a9d5aa789223c97944291`.
- Final classifier SHA-256:
  `d0f17cef2332663788ce69f9ade84d45580199d61a89fa4ec113e5ac14c7a9b5`.
- Independent auditor SHA-256:
  `8ef8e8abc4dfa2c20e00f1717e9253fbb3b00550b51a1c0a47f0788b7ddd8551`.
- Control-test SHA-256:
  `89f505333088bfc2f03ee05b8ae098fcd316e3f39de516dc2467af0b340a6cff`.
  Selected replay/audit image: `issue2849-py312-pytest-jsonschema:v1`,
  local image ID `sha256:5cc4d237e6af4548147ddfffc35413faf2487fd585f6a0216221f153f61cf073`.
  `DOCKER_CONTEXT=orbstack`, `--network none`; inputs are bind-mounted
  read-only. No host IPC directory is mounted.
- **C:** PASS can establish only this frozen saved-stream classification,
  parsing, schema validation, and receipt behavior. It cannot establish live
  endpoint compatibility, semantic quality, GUI behavior, task success,
  six-task acceptance, or efficiency.
- **U:** Any hash drift, invalid/ambiguous stream, audit disagreement, or
  unexpected external call is STOP/FAIL; do not retry the source model call.
  Preserve the predecessor and its formal failure unchanged.

## Source closure

- Base source: repository `origin/main` at freeze, recorded in
  `evidence/replay-v1/freeze.json`.
- Predecessor bundle: `research/integration/issue_2849_orbstack_real_model_preflight_v1/`.
- All added files for this replay are confined to this directory.
- Bytecode generation is disabled. Manifest policy excludes only the manifest
  itself and explicitly rejects cache files; the replay does not mutate the
  predecessor or its bundle.
- Construction controls invoke the classifier without frozen-input
  enforcement; the actual replay CLI always enforces both exact registered
  input hashes.

## Frozen command and outcomes

To be completed after the single registered replay. The command, exit codes,
image identity, source hashes, and independent decision will be recorded in
`RESULT.md` and `evidence/replay-v1/`.
