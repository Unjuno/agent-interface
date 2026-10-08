## Posthoc audit freeze and collision refresh — before any container invocation

The separately frozen read-only audit is on `research/issue-4485-posthoc-audit-20260926-r8n2`, freeze commit `e64917de74aa2c066b7b029d2a33028c45ee6300`; `FREEZE.json` SHA-256 `dbd139cc2d5f7f7372ee3f58beb39a141546b615880e3667074db0314b0a3e4f`, GitHub blob `e2583b2e0c09ba1b13cbbd2066ab455ee77af336`. The input evidence commit/tree was remotely re-read as `3fd9659d0e8c15beb794f8df769ca5235e6f43e2` / `5e974d0f13b145ef6739ebcab6472dd713cd5016`; original audit manifest is pinned at 50 raw files.

Fresh main is now `a61aa8f2991f537807e195e0bbf73ed309fcccfc`; README, CURRENT_GOAL, ROADMAP, RESEARCH_METHOD, and ISSUE_FAILURE_CLASSIFICATION are unchanged from the inspected d50eade base. Open-PR/branch refresh found #4497, a separate collision chronology record for a nonconforming invocation. It does not touch the authoritative 3fd9659d raw input or this read-only audit path; its rows remain excluded. The audit branch has no open PR or path collision.

Obstac gate: pinned OrbStack image resolves by digest to the frozen image ID on linux/arm64. One mock-free construction invocation is budgeted, followed by exactly one read-only raw audit invocation; broker/fake/model calls remain zero. Any posthoc PASS will not change this Issue allocation STOP. No container invocation has occurred yet.
