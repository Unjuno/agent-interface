# Construction and pre-formal failure chronology

- First Docker construction-suite attempt stopped during import with an
  `IndentationError` in `runner.py` after the COW capture refactor. No test body,
  optimizer, or formal cell ran. Indentation corrected.
- Second attempt stopped during import because both modules tried to set
  PyTorch inter-op threads after initialization in the shared construction
  process. No test body, optimizer, or formal cell ran. Runner initialization
  now tolerates the construction-only shared import; formal runner/auditor
  remain separate processes/containers.
- Corrected offline Docker construction suite passed 10/10 under both 1-vCPU
  and 2-vCPU quotas. The live `/sys/fs/cgroup/cpu.max` values matched each
  expected quota. These tests perform zero optimizer steps and consume no
  formal allocation.

The two initial errors are retained here rather than treated as formal STOPs.
No issue seed, model fit, inference schedule, or result was consumed by either
failed import.
