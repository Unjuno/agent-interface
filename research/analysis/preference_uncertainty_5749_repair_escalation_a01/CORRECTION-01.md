# Formal01 contract discrepancy and preservation

Formal01 candidate/auditor exited successfully and the auditor accepted 28 rows under its own policy oracle. A post-run cross-check found that the fixture's declared expected outcome for `known_locus_uninformative` was `targeted`, while both candidate and auditor accepted a candidate offer based only on one remaining candidate record. The auditor did not bind each case's declared expectation fields to its reconstructed output. Therefore formal01's PASS is retained as an output of its frozen implementation, but **not treated as a valid Issue-method result**. Its freeze, raw, audit and wiring STOP remain byte-for-byte unchanged.

Formal02 is a new allocation with an explicit `offer_allowed` field, exact row-level policy reconstruction, and an additional mutation that changes a declared expected outcome. It does not amend, erase, or relabel formal01. No retry of the formal01 candidate or auditor occurred.

Preserved formal01 hashes: original fixture `707a034ed04008354a8f709b64a35390f451afa61ec1cd7b7328e7acf0c92dd1`, raw `0e7083f32fa898fe59297df77dc9c013b0abab92ce4d22cd8116d37b7c6d3075`, audit `a79ed04a3a947221a40e1a8966a3ab45bf77975aa0299b01281f841eeada893b`. Formal02 `SHA256SUMS` verifies these predecessor files as well as its own package.
