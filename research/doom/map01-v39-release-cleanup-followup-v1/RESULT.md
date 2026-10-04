# Result

The initial parents (`2834209601483503a316863cf9964c9f966cede5` and `90e65c932a8a487d9657713e5a243cba25125c4f`) failed the three malformed-history/bracket tests. PR #7399 added owner-history validation, so this follow-up now stacks on exact head `f63f673538690fe6d6661a22d894cf1c061d3385`. Its malformed or reversed caller-bracket regression still failed there, leaving `ordinary_release_candidate=True`. The follow-up requires ordered integer bracket endpoints; invalid timing evidence now forces the per-key ordinary candidate and batch verification false.

After rebasing on PR #7399, candidate checks passed again: backend suite 26/26, adjacent owner-wrapper suite 8/8, byte-compilation, and `git diff --check`. The independent saved-log auditor checks all parent RED receipts, candidate suite runs, exit receipts, expected regression names, contradictory-output mutations, and the initial frozen parent source hashes.

This is a local construction repair on PR #7385's exact code lineage. It does not establish physical X11 release, useful application feedback, bounded recovery, a live-control result, or a new formal allocation. The predecessor's raw experiment logs and hashes remain unchanged and apply only to the frozen parent source.
