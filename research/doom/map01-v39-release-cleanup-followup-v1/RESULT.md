# Result

Both the initial parent (`2834209601483503a316863cf9964c9f966cede5`) and refreshed stacked parent (`90e65c932a8a487d9657713e5a243cba25125c4f`) failed all three added adversarial tests: malformed cleanup timestamp, malformed owner history row, and malformed release bracket each left `ordinary_release_candidate=True`. The repaired adapter marks cleanup history valid only when every row is a dictionary and each `owner_release` has an integer `verified_ns`; it also requires each caller bracket to contain ordered integer timestamps. Any invalid evidence forces the per-key ordinary candidate and batch verification false.

After rebasing on the refreshed parent, candidate checks passed again: backend suite 24/24, adjacent owner-wrapper suite 8/8, byte-compilation, and `git diff --check`. The independent saved-log auditor checks both parent RED receipts, both candidate suite runs, exit receipts, expected regression names, contradictory-output mutations, and the initial frozen parent source hashes.

This is a local construction repair on PR #7385's exact code lineage. It does not establish physical X11 release, useful application feedback, bounded recovery, a live-control result, or a new formal allocation. The predecessor's raw experiment logs and hashes remain unchanged and apply only to the frozen parent source.
