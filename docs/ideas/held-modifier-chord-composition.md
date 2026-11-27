# X11 chord composition with an already-held modifier

- **Status:** Initial held-nonmodifier refusal merged; a later review found a remaining paced-text prefix effect.
- **Source:** Issue [#8252](https://github.com/Unjuno/agent-interface/issues/8252), related to #574/#57.
- **Idea:** Test whether an X11 chord releases a modifier already held by the same backend, and whether preflight prevents partial emission when a text plan later encounters a held-key conflict.
- **Outcome:** Merged [PR #8308](https://github.com/Unjuno/agent-interface/pull/8308) adds refusal for a held nonmodifier before direct chord emission and covers several focused cases. Exact-head review then demonstrated a remaining composition gap: after `hold-a`, `text("ba", gap_ms=1)` can emit/release `b` before refusing `a`. Cleanup restores neutral state but cannot undo that prefix. Whole-program preflight must account for held keys, preceding holds/releases, and expanded text. No Xvfb actor, game, or live application result was produced; the open Issue's correction remains unresolved.
