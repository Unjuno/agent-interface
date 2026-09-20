# Docker model-output schema preflight

The preflight is a narrow endpoint gate, not a task-success or GUI-authority
result. It can return `PASS` only when the host-model IPC runner produced exactly
one completed turn and exactly one `agent_message`, whose text parses as JSON and
passes the supplied JSON Schema. The schema is selected using its declared
`$schema` dialect; malformed schemas, undeclared/unsupported dialects, remote
references, and unavailable validation dependencies stop explicitly. Local
references are resolved from the supplied schema only. The validator's
`referencing.Registry` also has an explicit retrieval callback that refuses all
external fetches, independent of the structural remote-reference precheck.

The retained report includes the actual usage object when present and a SHA-256
of the model-response text. Invalid responses retain only the validator keyword
and instance path; validator messages are omitted because they can echo the full
model output. No model answer is itself authority or task success.

Offline verification:

```sh
python -m pip install -r runtime/requirements-docker-schema-preflight.txt
python -m unittest runtime.test_docker_schema_preflight_v1 -v
```

These contract tests use synthetic event streams and do not start Docker, call a
model, launch a GUI, or issue input. Actual Docker/host-IPC execution remains a
separate gate under Issue #2849.

The integrated-efficiency Docker backend also applies this validator to its
retained events using the explicitly configured Docker schema before semantic
contract parsing. A failed gate retains `schema-validation.json` and stops
without parsing or retrying the model call. Runner stdout/stderr and successful
parsed `result.json` are retained alongside the raw runner files. The existing
plain/compiled semantic validators still run after schema validation; a schema
PASS alone does not establish task correctness. Install the pinned validator in
the Python environment invoking this backend as well as any preflight environment.
