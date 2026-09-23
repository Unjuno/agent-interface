# Branch-only compute run retention

Temporary GitHub Actions workflow was added only on the research branch and removed before this result PR. It never appears in the final base-to-head diff.

- workflow run: `35096754461`
- job: `104795892358`
- compute commit: `f2371d9a94f180f71356a3f4419ca3988a348b27`
- runner image: Ubuntu 24.04, Actions runner `2.337.0`
- checkout commit verified by workflow log: `f2371d9a94f180f71356a3f4419ca3988a348b27`
- existing analyzer regression: `PASS 7 tests`
- first computation failure: `AssertionError: started hold never reached keys_held: ('cover-4', 10)`
- `result.json`: not produced
- artifact upload: skipped
- formal/live/model/input/game execution: none

The workflow also exposed a supervision defect: compute and audit commands were piped through `tee` without shell `pipefail`, so GitHub marked those individual steps successful despite Python tracebacks. The later hash step failed because the expected result file did not exist. This branch does not repair or rerun that workflow. The Python failure and missing result are authoritative.
