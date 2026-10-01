# Separate successor allocation — Issue #5330

The first allocation `...-01` is retained unchanged as `STOP_RUNNER_IMPORT_ROOT`; it was never retried. This new allocation `constrained-interaction-5330-t0-20260930-02` corrects only the container import-root setup. The question, factor levels, planted synthetic pair/triple controls, covering-design algorithm, metrics, and pass/fail/STOP criteria are unchanged. This is not a retry of formal-01: it has a new allocation identity, new freeze, and previously absent output path `results/formal-02/`.

Image `python:3.12-slim`, exact ID `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, linux/amd64. Mount the repository's `research/` at `/workspace/research` read-only, set working directory and `PYTHONPATH` to `/workspace`, and mount only the absent `results/formal-02/` as `/out`. Network is disabled, root filesystem read-only, capabilities dropped, no-new-privileges. Python 3.12.14, standard library only.

One frozen formal invocation: `python -B -m research.analysis.constrained_interaction_testing_5330_t0_v1.run /out/formal-02`. Only on exit 0 and a raw artifact, run the separate raw-only auditor once: `python -B -m research.analysis.constrained_interaction_testing_5330_t0_v1.audit /out/formal-02/raw.json`. No retries. Source hashes are in `FREEZE_V2.json` and match the unchanged code files from the first freeze.

All claims remain synthetic design sensitivity only. Neither a pass nor a fail establishes real runtime safety, hazard prevalence, or production interaction coverage.
