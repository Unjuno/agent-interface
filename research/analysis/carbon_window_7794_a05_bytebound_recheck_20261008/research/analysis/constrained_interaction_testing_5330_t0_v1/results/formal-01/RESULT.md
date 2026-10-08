# T0 result — Issue #5330

Disposition: **`STOP_RUNNER_IMPORT_ROOT`**. The one frozen Docker invocation exited 1 before importing the runner. The exact invocation, image, Python error, missing output, and no-retry disposition are preserved in [`STOP.json`](STOP.json). No matrix ran, no raw assignments were produced, and the independent-audit gate was not reached. Do not describe the synthetic sensitivity hypothesis as experimentally supported by this allocation.

The runner was invoked with the package subdirectory mounted as `/src` and `/src` as the working directory. Python consequently could not resolve the repository-level `research` package: `ModuleNotFoundError: No module named 'research'`. The pre-run seven host construction tests verified the design but did not verify the container import root. This is an experiment setup failure, not evidence for or against constrained interaction testing.

The output directory was newly created immediately before the call and contains only this STOP record. No retry or repair was made under this allocation. A corrected mount/root requires a distinct successor allocation with a new freeze and absent output path.
