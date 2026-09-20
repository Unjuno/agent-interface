# Integration scope — 2026-09-21

This directory preserves the three original files from PR #3563, head
`3ebce103fce229fe59208dafbb7687e3d9a0d976`, without changing their bytes.
It is a historical producer-reported packaging smoke result, not a fresh
current-main acceptance run or independently reconstructable raw-evidence bundle.

The recorded source is `52260e2c7f296771db3c9e725bbd0a427a4b014f`.
Its harness expects exactly two tools. Current main also exposes
`interface_results`; running the old harness against today's archive would stop
at tool discovery. Reproduction of the historical procedure requires the pinned
source and its dependencies. The README's build command alone does not pin that
source. Do not remove the assertion and describe a new run as the historical run.

The harness deleted its temporary reports, images and fixture output. Therefore
`result.json` and the recorded artifact digest cannot independently prove those
raw outputs or historical process cleanup. No new GUI action was performed for
this integration review, and no runtime behavior is promoted by adding this record.

## Current integration checks

The original branch merged without conflicts into main snapshot
`6b3c5fd93` in the integration worktree. Tests of that integrated tree:

- WSL Ubuntu, Python 3.12, MCP SDK 1.30.0:
  `python -B -m unittest runtime.cli_v1.test_mcp_server runtime.selector_v1.test_selector -q`
  — 26 passed. This includes actual portable stdio initialization outside the
  checkout and current tool discovery, plus controlled backend failure handling.
- Windows Python:
  `python -B -m unittest runtime.distribution_v2.test_distribution -q`
  — 6 passed.

An initial combined WSL run had four distribution errors because Linux Git
cannot resolve this Windows worktree's drive-letter `.git` reference. This was
an environment failure, retained here rather than counted as a passing Linux
distribution test. The distribution suite was subsequently run on Windows,
where the worktree's Git metadata resolves correctly.

These checks establish the tested packaging/transport contracts only. They do
not establish current live GUI task success, host presentation, model-visible
feedback latency, model-token savings, or the broader #3370 acceptance gate.
