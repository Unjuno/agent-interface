# C02 post-run correction — invocation count

This additive correction does not edit or replace the original C02 EXECUTION.json, REPORT.md, source, or first outcome.

The GitHub Actions log for run 37808378273 shows the candidate shell failed at redirection, before Python started:

```
...sh: line 1: research/analysis/cue_feedback_8654_c02_20261009/results/candidate_stdout.json: No such file or directory
Process completed with exit code 1.
```

The results directory was not created before the shell opened candidate_stdout.json. Therefore the authoritative process counts are candidate=0, auditor=0. The original EXECUTION.json's candidate_invocations=1 is an inaccurate step-level inference; preserve it as first committed and use this correction as the controlling clarification. No raw JSONL was generated or uploaded, no auditor ran, and the scientific hypothesis was not evaluated. The workflow reported STOP_CANDIDATE_FAILED; the artifact upload and auditor were not reached successfully. No candidate or auditor retry occurred.

The independent C03 allocation uses a new branch, new source freeze, and additive output path, and pre-creates its output directory before invoking Python. It is the first candidate execution for this still-untested hypothesis, not a rerun of C02. C02 remains an infrastructure STOP and remains unchanged.
