# Local development checks (not formal Docker evidence)

Host: macOS 25.6 arm64, Python 3.14.5. These checks exercised the code path locally before formal container allocation; they do not satisfy the preregistered Docker candidate/auditor invocation.

Commands:

```sh
python3 -m unittest -v test_gate.py
python3 -m py_compile candidate.py audit.py workflow_gate.py workflow_runner.py test_gate.py
python3 -m json.tool fixtures.json
python3 -m json.tool FREEZE.json
ruby -e 'require "yaml"; YAML.load_file("../../../.github/workflows/issue-5686-surrogate-gate-t0.yml")'
python3 candidate.py --input fixtures.json --output raw/development/candidate.jsonl
python3 audit.py --input raw/development/candidate.jsonl --fixtures fixtures.json --output raw/development/audit.json
python3 ../check_index.py
git diff --check
```

Observed before formal freeze: 3/3 unit tests passed; compilation passed; candidate emitted 24 attempts across 5 worlds; the independent audit returned `PASS_SURROGATE_GATE_SCOPED` with zero errors; the two corruption tests failed closed as expected. The repository analysis-index check passed with 258 retained result directories. Development artifacts are preserved under `raw/development/`. Final local CI must be rerun after the formal run and report/index update. Formal container runs are deliberately isolated in separate digest-pinned workflow jobs because local OrbStack currently has unresolved nonterminal containers; host development checks do not count as the formal result.
