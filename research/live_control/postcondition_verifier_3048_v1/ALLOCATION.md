 #3048 deterministic postcondition allocation
Date: 2026-09-20 Asia/Tokyo
Image: mixed-formal-3025:20260920
Network: disabled; fresh container.
Frozen matrix: 10 cases covering three valid postconditions, accepted-no-effect, wrong-target, stale, ambiguous receipt, missing effect, pixel-only, and cleanup failure.
Result: FAIL_POSTCONDITION_BOUNDARY.
Three valid cases agreed and six corruption controls were fail-closed, but independent audit disagreed with verifier on wrong_target and missing_effect. No rich-agent/model/network calls (0/0).
Source hash: 5487047614fc9268306a9c086bc47816b3158a08dc07b013667ef4c4333c917a
Result hash: 05768d240aadfe8576e393f77a76190f52d3dece5843b88dc8c6d51cede53949
Interpretation: verifier contract is incomplete; do not claim deterministic boundary PASS.
