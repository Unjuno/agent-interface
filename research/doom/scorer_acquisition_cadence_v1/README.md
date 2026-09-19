# Scorer acquisition/cadence research

Start with REPORT.md and FREEZE.json. All new files are an isolated research candidate; historical runtime bytes remain pinned to 9e6d5ecd, not silently rebased onto publication main.

Repository-only checks:

```sh
python test_acquisition.py
python audit_endpoints.py
```

Full replay: extract the separately delivered evidence ZIP into a NEW workspace, not over a normal repository/product `runtime/` directory. It includes the recorded runtime source closure but not all engine wheels or a full fresh-execution environment. In the extracted workspace:

```sh
CODE=research/doom/scorer_acquisition_cadence_v1
python "$CODE/replay.py" .
AI_PREFLIGHT="$PWD/preflight-02" python -m unittest discover -s "$CODE" -p 'test_*.py'
python "$CODE/audit_ledger.py" "$CODE/results/measurements.json.xz"
```

Pixel replay requires Pillow; endpoint/ledger replay uses only the standard library. Without AI_PREFLIGHT the 12 retained-preflight mutation tests skip explicitly, not pass. The full ZIP includes plan.json and results/summary.json plus all controller/scorer traces, PNG/AIT images, setup failure, manifests and exact sources. GitHub retains selected raw numeric endpoints and exact executable source/plan/report; full raw evidence and the compressed 494-row ledger are conversation attachments bound by archive.json, not claimed uploaded to GitHub/Actions.

For a NEW live experiment, use the fixed source/wheel bundle documented in REPORT.md, check every dependency/hash, create a new plan and new output IDs. Never rerun this consumed allocation or overwrite its first outcomes. The driver enforces local output nonexistence only; it is not a cross-host single-execution guard.
