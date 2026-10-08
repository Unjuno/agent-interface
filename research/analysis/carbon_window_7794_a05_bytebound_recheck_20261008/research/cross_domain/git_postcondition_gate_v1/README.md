# Candidate postcondition experiment

Read REPORT.md for scope and interpretation. This is additive research, not production code.

## Replay retained measurement (does not rerun live cases)

```sh
python source/audit.py source/plan.json measured reproduced-result.json
```

This audit uses only Python's standard library and the retained Git loose objects.

## Unit/construction tests

```sh
cd source
python -m unittest -v test_contract
```

Tests create24 temporary native-Git construction cases, distinct from the measured allocation.

## New local reproduction

```sh
python source/experiment.py source/plan.json NEW_EMPTY_OUTPUT_DIRECTORY
python source/audit.py source/plan.json NEW_EMPTY_OUTPUT_DIRECTORY new-result.json
```

For an independent study, make a separately labelled plan/allocation first and preserve its own freeze. Do not overwrite the supplied `measured` directory. The runner refuses reused case directories and checks all executable source hashes. Tested: Git2.47.3 and Python3.13.5, local bare SHA1 repositories. No external Python package is required. No repository, file, network or GUI outside the chosen new output directory is modified.

GitHub publication occurred after the local frozen allocation because connector write actions were unavailable during execution. Local freeze is not remote preregistration. Full raw Git objects remain in the conversation evidence archive; GitHub retains source, exact plan, report, compact results and validation metadata.
