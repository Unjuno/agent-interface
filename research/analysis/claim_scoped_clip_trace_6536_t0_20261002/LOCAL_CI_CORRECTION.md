# Local CI invocation correction

The first exploratory local CI pass was started after temporarily appending this package's test command to `.github/workflows/analysis-index.yml`. Two pre-existing frozen-provenance tests correctly failed because that file's hash changed from the pinned `b19000e027e7379ef6c0122e3f8cfd0b2faacb4c54d985ab87d27c1be914f7c2` to `0d40e7b2e50055da73eef87318ab4efac3cd3e7e18686d648f00abf045606b71`. The workflow edit was removed; the repository workflow remains unchanged.

One nested test also failed because it was launched from the repository root rather than the workflow's declared `research/analysis/human_return_resumption_6492_t0_20261002` working directory. It is rerun below using that exact working directory. Neither condition touched the frozen candidate/auditor source, fixture, or retained first output. The T0 test suite itself passed during the initial pass and is included in the corrected local suite rerun.
