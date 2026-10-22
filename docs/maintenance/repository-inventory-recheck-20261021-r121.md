# Repository membership recheck r121 — 2026-10-21

At 2026-10-20 15:52 UTC, `main` was `093be6c88c3f728897f168422ae0c58d4cd86b91` before and after complete paginated CLI reads (`gh issue list --limit 2000`, `gh pr list --limit 1000`). The counts and sorted ID sets were compared with the full row-level metadata in [r120](repository-inventory-recheck-20261020-r120.md).

| Set | Current rows | Sorted-ID SHA-256 | Difference from r120 |
|---|---:|---|---|
| Open Issues | 1,655 | `720d98407db3844e421e3e647bfec33889e90e842d1d3bd4b601c2db93a4faa9` | None |
| Open PRs | 466 | `fdacebfea0fbb9a216ff3d50aa6f9d89f5fceced0a775492aee2e9efeff29313` | #8841 only |

The r120 row exports remain reusable because the exact current sets equal r120's Issue set and its PR set minus #8841. This recheck adds no duplicate full export and establishes membership only; it does not refresh row metadata, semantic disposition, ownership, PR readiness, or workspace custody. Re-fetch each live record before a state change. The main commits since the r120 capture are documentation-only.
