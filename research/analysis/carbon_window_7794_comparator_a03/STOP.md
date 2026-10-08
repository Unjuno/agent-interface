# A03 terminal outcome — STOP_INFRA_CANDIDATE_OUTPUT_PATH

The frozen candidate command was submitted once as `python3 candidate.py > formal_a03/candidate.json`, but the shell failed before starting Python because the reserved `formal_a03/` directory did not exist (`zsh: no such file or directory: formal_a03/candidate.json`). The candidate script invocation count is 0; auditor invocation count is 0; retries are 0. No candidate output exists and no scientific inference is accepted.

This is a launch-path infrastructure stop caused by an output-directory setup omission. It is not `FAIL_METHOD` and says nothing about the comparator hypothesis. Preserve the frozen source, input, and this first terminal record unchanged; do not retry this allocation. A separately frozen future allocation would need explicit new ownership and a precreated, verified output directory before formal launch.
