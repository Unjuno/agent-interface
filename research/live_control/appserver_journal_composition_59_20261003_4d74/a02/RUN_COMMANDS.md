# A02 recorded commands

Use frozen run_once.ps1 with Phase construction02, then producer-a02, then audit-a02 only when producer exit0. The launcher refuses an existing receipt directory and records argv, UTC, client PID, exit code, stdout/stderr as UTF-8 host-decoded text. Exact guest peer/worker bytes remain .bin artifacts.

Each command uses installed WSLc cached image sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4 with --pull never --network none --cpus0.25 --memory512m --user65534:65534, PYTHONDONTWRITEBYTECODE=1. Source mount is read-only; output is fresh. Candidate staging contains only seven source_sha256 source files plus fixture.json; auditor/scoring and prior A01 outputs are absent.

construction_checks.py --fixture/src/fixture.json
producer.py --fixture/src/fixture.json --out/out/raw.json
auditor.py --fixture/src/fixture.json --raw/results/raw.json --source-dir/src --out/out/audit.json

The literal separated argv is defined in run_once.ps1 and retained by command.json, not the condensed command notation above. Source/image identity, owner/collision, current main and absent-output gates precede invocation. Memory/cgroup warnings are preserved; requested configuration alone does not establish enforcement.
