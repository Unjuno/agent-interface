# Local checks

Run the package-only contract tests without starting Docker or ViZDoom:

```sh
python3 -m unittest discover -s research/doom/map01_attack_start_gate_4223_t6_20261001 -v
python3 -m py_compile research/doom/map01_attack_start_gate_4223_t6_20261001/*.py
git diff --check
```

The actual candidate is intentionally not simulated by these checks. Local
OrbStack was unavailable during this allocation; the one real candidate and
raw-only audit are run by the one-shot Linux/amd64 Docker workflow on PR-open.
An Actions green check without the candidate artifact and independent audit is
not a result.
