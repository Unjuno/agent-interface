# Native SVG scoped-edit research evidence

Issue #344. These are native Inkscape command-line actions and local Git publication experiments, not production GUI/Executor integration. All files are additive research evidence.

`source.tar.xz` contains byte-exact experiment.py, audit.py, test_contract.py, run_block.py, environment and original plans/freezes. Extract it into a new directory for source review. Source/plan hashes are bound by the separately committed FREEZE_A/A2/B files; local freeze JSONs and their publication wrappers have additional descriptive-field differences, not source/plan differences.

REPORT.md records incomplete allocation A, complete A2/B, negative controls and interpretation limits. RESULT.json and CASE_VERDICTS.csv separate correct refusals from successful edits. ARTIFACTS.json distinguishes the source archive retained here from full native repositories/logs/SVG/PNG evidence delivered only as a conversation attachment.

Offline replay from the extracted FULL conversation evidence bundle:

```sh
python source/audit.py measured_A2 source/plan_A2.json replay-A2.json
python source/audit.py measured_B source/plan_B.json replay-B.json
(cd source && python -m unittest test_contract -v)
```

The auditor does not rerun measured cases. Tests create separate temporary construction repositories and invoke native Inkscape. New live experiments require new allocation/case IDs and a new freeze; do not reuse consumed measured directories. The original A prefix is never pooled into A2.

Dependencies: Inkscape1.4, Git2.47.3, CPython3.13.5, lxml6.1.1 and Pillow12.3.0; measured native locale C.UTF-8. No fonts or installed binaries are redistributed.
