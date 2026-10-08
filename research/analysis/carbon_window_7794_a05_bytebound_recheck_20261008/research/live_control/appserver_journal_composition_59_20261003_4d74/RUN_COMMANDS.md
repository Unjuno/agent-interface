# Frozen WSLc commands

The exact local image ID is checked against its repo digest before each invocation. Source root <study> is readonly; candidate source root <candidate-input> contains only the seven code files and frozen fixture; each output directory is separate and new. PYTHONDONTWRITEBYTECODE=1. Preserve stdout, stderr, UTC boundaries and exit codes.

Construction (no formal cells):
wslc run --rm --pull never --network none --cpus 0.25 --memory 512m --user 65534:65534 --env PYTHONDONTWRITEBYTECODE=1 --volume <study>:/src:ro --workdir /src sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4 python -B /src/construction_checks.py --fixture /src/fixture.json

Producer (ONE invocation):
wslc run --rm --pull never --network none --cpus 0.25 --memory 512m --user 65534:65534 --env PYTHONDONTWRITEBYTECODE=1 --volume <candidate-input>:/src:ro --volume <candidate-output>:/out --workdir /src sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4 python -B /src/producer.py --fixture /src/fixture.json --out /out/raw.json

Auditor (ONE invocation, only if producer exits0):
wslc run --rm --pull never --network none --cpus 0.25 --memory 512m --user 65534:65534 --env PYTHONDONTWRITEBYTECODE=1 --volume <study>:/src:ro --volume <candidate-output>:/results:ro --volume <audit-output>:/out --workdir /src sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4 python -B /src/auditor.py --fixture /src/fixture.json --raw /results/raw.json --source-dir /src --out /out/audit.json

## Recorded host invocation

Run the frozen run_once.ps1 with exactly one Phase per role: construction01, producer-a01, audit-a01. It refuses an existing receipt directory. It starts installed WSLc without a visible helper window and retains argv, UTC, client PID, exit code and UTF-8 host-decoded console logs. Guest raw peer/worker .bin files retain exact bytes. Candidate staging contains only the seven source_sha256 files plus fixture.json; auditor and truth are excluded.
