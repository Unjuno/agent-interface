# Local development checks (not formal Docker evidence)

Local host: macOS arm64, CPython 3.14.5. This host run is development validation only; formal candidate and raw-only auditor run once in separate pinned Docker jobs because the shared OrbStack lane remains unavailable under Obstac.

Commands from this directory:

```sh
python3 -m unittest -v test_gate.py
python3 -m py_compile candidate.py audit.py test_gate.py workflow_gate.py workflow_runner.py
python3 -m json.tool fixtures.json
python3 -m json.tool FREEZE.json
ruby -e 'require "yaml"; YAML.load_file("../../../.github/workflows/issue-5686-surrogate-selection-t2.yml")'
python3 candidate.py --input fixtures.json --output /tmp/candidate.jsonl
python3 audit.py --input /tmp/candidate.jsonl --fixtures fixtures.json --output /tmp/audit.json
python3 ../check_index.py
git diff --check
```

The formal result is distinct from these host checks and must include all raw outputs, source/image/exit evidence, and independent audit. Do not overwrite existing formal or predecessor artifacts.
