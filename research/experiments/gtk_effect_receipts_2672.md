GTK effect-receipt preflight (#2672)

Local Docker codex-gtk-model:local with GTK3 + Xvfb, fixed eight-case order. The in-place GTK rendering attempt failed and is preserved in #2671. The corrected runner creates a fresh GTK window for the post-effect observation, then compares drawable hashes independently.

Result: scorer_matches=true. Actual dispositions exactly match expected: SUCCESS, YIELD, YIELD, NONE, PARTIAL, YIELD, YIELD, YIELD.

The raw local artifact includes before/after drawable hashes, event trace, input ledger, authority lease, independent effect receipt, cleanup receipt, and scorer output. This is a bounded local fixture preflight only, not formal #2606 acceptance, production adapter integration, or proof of provider/model utility.