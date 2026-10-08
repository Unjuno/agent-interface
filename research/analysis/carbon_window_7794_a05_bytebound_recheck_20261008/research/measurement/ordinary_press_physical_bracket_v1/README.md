# Ordinary press physical bracket contract v1

Issue: #994  
Task: `ORDINARY-PRESS-PHYSICAL-BRACKET-CONTRACT-20260917-001`  
BASE: `e6ff338055099f92650a3d978374b5d9271a3353`

Decision: **PASS_PHYSICAL_PRESS_BRACKET_CONTRACT_SCOPED**

A new physical key-down interval is exposed only when the owner did not already hold the key, a physical pre-sample reports UP, one KeyPress is attempted and sync succeeds, a physical post-sample reports DOWN, owner state records the key after admission, and timestamps/lineage are valid. The interval is exactly `[pre_sample_end,post_sample_end]`.

Construction used an independent truth-table oracle: exhaustive256 cases over all six evidence booleans and four timestamp spacings, plus200,000 seeded random cases. Candidate/oracle mismatches0; contradictory cases rejected64; fixed parent/ablation/malformed controls16/16; random confirmed intervals3,040; false physical intervals0. Digest `48aab7b589a0b61992e818aa447c44f75fa53ff8e14bd72250b422a99ef95058`.

Container diagnostics: wall6.41s, max RSS92,972KB; no performance claim.

SHA-256: contract `f769fddb546522a0fe3e5c068e5c9aa9e3e0eaba7114b90a9f0a7e5a7b638d47`; test/oracle `908c58e7a7ed35e694eff266cada05d547d56a50c29e74b901345357a5e1ccf1`; result `9959835a9d4b98bbc4bcaf974d9affefffe469e26e6e7f7fd5e7759722b6cb85`.

This is a conservative temporal bracket, not causal proof. Preexisting physical DOWN and owner-already-held states never count as a new down edge. Actual X11 instrumentation remains separate.
