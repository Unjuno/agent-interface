# #3311 local host-IPC path boundary experiment — 2026-10-05

Code basis: `origin/main` at `2f2c83c3da36566bac410b13b2ed5202c9641f1a`, plus
the candidate changes in branch `research/3311-host-ipc-boundary-20261005`.

## H — hypothesis

When the real host IPC runner and broker execute as local processes against an
inert fake CLI, the staged `/repo` path map will resolve the exact frozen
runner/schema/instructions/prompt/workspace inputs on the host, return one
schema-valid response, and grant no desktop-input authority.

## T — bounded test

Executed one fresh local process round-trip with the repository's actual
`container_host_model_ipc_runner_v1.py` and `runtime/host_model_ipc_broker_v1.py`.
The fake CLI asserted that the mapped schema and workspace existed, then emitted
one `thread.started`, one schema-compatible message, and one synthetic usage
event. The broker used `--once`. The predeclared pass conditions were: both
processes exit 0; one matching request id; source and path-map hashes match;
broker-resolved schema/workspace paths equal the inputs; response bytes match
the runner event bytes; JSON Schema accepts the response; and request and broker
receipts both deny authority.

This test ran as local subprocesses. No Docker container, real model, GUI,
application task, or native input was used. The fake CLI made no network call,
but network isolation was not enforced at the operating-system level; this
result therefore does not establish a Docker `--network none` gate.

## D — observed result

The successful attempt is `evidence-02/`. Runner and broker both exited 0 for
request `87f277fdd5fc4514bc2a479355dfdf19`. The response round-tripped byte for
byte, validated against the recorded schema, and used the exact staged schema,
instructions, prompt, runner, and workspace targets. The separate raw-only
audit script returned `PASS_BOUNDARY_ONLY` with zero errors; all five
path-map target checks and all five source-hash checks passed. The request and
broker receipts both record `authority_granted=false`. Synthetic usage fields
in the fake event were input=5/output=2; these are test values, not provider
usage. The verifier is separate code that reads the raw receipts; it was written
in this task and is not an independent person or blinded task-effect auditor.

## C — decision

`PASS_BOUNDARY_ONLY`. This supports the local process-level IPC and host path
mapping contract for this inert case. It does not prove Docker bind-mount
behavior, image identity, model endpoint compatibility, desktop safety,
correct task effects, or any efficiency benefit. It does not consume or replace
the frozen #3311 three-arm allocation.

## U — unresolved / stop conditions

The formal allocation remains `HOLD_PLATFORM_IMAGE_UNAVAILABLE`. The current
OrbStack daemon is the only discovered Docker engine; its prior matching-client
image inspection failed in the content store. OrbStack also has active machines
whose owners/release windows are unverified. Do not launch the three-arm run
until the pinned image is verifiable and an exclusive runtime window is
established. The remaining Issue #3311 deliverables are an actual cold/warm/
invalidation/repair comparison, provider usage and timing, independent task-
effect audit, raw model/container receipts, and final H/T/D/C/U report.

## Reproduction and evidence integrity

From the repository root:

```sh
python3 -m venv /tmp/issue3311-audit-env
/tmp/issue3311-audit-env/bin/python -m pip install \
  -r runtime/requirements-docker-schema-preflight.txt
PYTHONPATH=research/live_control \
  /tmp/issue3311-audit-env/bin/python research/integration/issue3311_host_ipc_path_boundary_main_20261005/run_experiment.py \
  /absolute/path/to/a/new/output-directory
PYTHONPATH=research/live_control \
  /tmp/issue3311-audit-env/bin/python research/integration/issue3311_host_ipc_path_boundary_main_20261005/audit_experiment.py \
  /absolute/path/to/the/output-directory
/tmp/issue3311-audit-env/bin/python research/integration/issue3311_host_ipc_path_boundary_main_20261005/seal_evidence.py \
  /absolute/path/to/the/output-directory
/tmp/issue3311-audit-env/bin/python research/integration/issue3311_host_ipc_path_boundary_main_20261005/verify_evidence_manifest.py \
  /absolute/path/to/the/output-directory
```

The executed commands and raw receipts are retained in `evidence-02/`;
`evidence-manifest.json` covers 32 evidence entries and rechecked 32/32.
`source_sha256.json` pins the backend, runner, broker, schema validator, and
experiment harness. The audit script SHA-256 is in
`evidence-02/independent-audit.json`.

The experiment used a temporary source-root copy under `/private/tmp` to keep
the local account path out of the published receipts; the relative source
hashes all match this branch. The five staged host-path symlinks are represented
by their exact targets in `evidence-manifest.json` and corroborated by the raw
path-map, commands, and broker-resolved paths. Their absolute symlink nodes are
omitted from the checked-in tree so a clone does not materialize links into a
temporary host path. The path-target records themselves remain hashed.

The focused latest-main regression command and raw unittest output are retained
in `VALIDATION.md` and `focused-tests.stdout.txt`.
