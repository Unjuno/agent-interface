# Docker model-output schema preflight

The preflight is a narrow endpoint gate, not a task-success or GUI-authority
result. It can return `PASS` only when the host-model IPC runner produced exactly
one completed turn and exactly one `agent_message`, whose text parses as JSON and
passes the supplied JSON Schema. The schema is selected using its declared
`$schema` dialect; malformed schemas, undeclared/unsupported dialects, remote
references, and unavailable validation dependencies stop explicitly. Local
references are resolved from the supplied schema only; the validator never
fetches remote schema content.

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
