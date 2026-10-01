# Local validation

Run local structural checks (no game candidate) before the one-shot hosted
allocation, then repeat after adding its evidence/report:

```sh
python3 -m unittest discover -s research/doom/map01_attack_start_gate_4223_t10_20261001 -v
python3 -m py_compile research/doom/map01_attack_start_gate_4223_t10_20261001/*.py
git diff --check
python3 research/check_workspace_index.py --git-tree
```

Also validate YAML with the system Ruby/Psych parser, check the source digest
manifest with `shasum -c`, and run `git diff --check` plus the workspace index
check. After the run, verify the downloaded workflow ZIP against GitHub's exact
size/digest metadata and `unzip -t`; run
`(cd research/doom/map01_attack_start_gate_4223_t10_20261001/evidence && shasum -a 256 -c EVIDENCE_SHA256SUMS.txt)`.
These checks are not experimental evidence. The candidate runs exactly once
through `orchestrate.py`; its source/image identities, logs, raw receipt and
conditional independent audit are retained in `REPORT.md` and `evidence/`.
