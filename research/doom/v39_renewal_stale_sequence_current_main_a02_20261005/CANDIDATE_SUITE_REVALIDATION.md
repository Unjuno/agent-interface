# Candidate suite revalidation — fc14994

Using the exact controller snapshot extracted from commit `fc14994f53655da57b9b6573d028ddde1a11b858`, the retained candidate wait suite and focused stale-renewal suite were re-run from a temporary directory with the filenames expected by the tests and that directory on `PYTHONPATH`.

- `python -m unittest -v test_overlap_controller_v39_wait`: 15/15 PASS.
- `python -O -m unittest -v test_overlap_controller_v39_wait`: 15/15 PASS.
- `python -m unittest -v test_v39_soft_stale_renewal_v1`: 4/4 PASS.
- `python -O -m unittest -v test_v39_soft_stale_renewal_v1`: 4/4 PASS.

Two preliminary attempts failed before assertions because the extracted tests could not find/import their expected sibling source/module from the A02 directory and because Python's import path retained the parent working directory. They do not indicate candidate assertion failures. The corrected layout and invocation above passed all four runs. Temporary files were outside the repository; no production source was modified.

This still does not execute the full planner/executor/game/scorer/cleanup runtime or establish task effect. Candidate A01 records the broader controller suite could not import due to missing Pillow.
