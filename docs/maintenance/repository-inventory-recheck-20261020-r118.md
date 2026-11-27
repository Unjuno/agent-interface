# Repository membership recheck r118 — 2026-10-20

Captured around `2026-10-20 12:17 UTC` against GitHub `origin/main`
`6e2d1841646ef4a43ee91b043830c3a7b30eabed`, after PR #9265. The main SHA was
read before and after the complete CLI membership and row-metadata reads and
remained stable. GraphQL total counts bracketed the reads. The CLI limit was
2,000, above both returned sets.

| Set | CLI rows | GraphQL before/after | SHA-256 of sorted newline-separated IDs | Compared with r117 |
|---|---:|---:|---|---|
| Open Issues | 1,672 | 1,672 / 1,672 | `073738bd5d54cc178a3f92d9df0d03d054a12968ccf5fd575ed57e8ee72e55d4` | ID set changed; count unchanged |
| Open PRs | 468 | 468 / 468 | `878a28d681a0ae705654b670693106498874c525afe2ca828aa129b3dccafb3a` | ID set changed; count unchanged |

Full row metadata is retained in [open Issues](open-issues-20261020-r118.json)
and [open PRs](open-prs-20261020-r118.json). A same count does not mean the ID
sets are unchanged; do not reuse r114 row metadata as current for an item
without checking that item's live record. This snapshot is not semantic triage,
ownership, PR readiness, or artifact-custody proof. Re-fetch the target and its
dependencies immediately before any state change.
