# #1337 full analyze interval-union integration

Decision: **PASS_FULL_ANALYZE_INTERVAL_UNION_EQUIVALENT_SCOPED**

One logical formal invocation, reruns/replacements/tuning0.

- exact #988 parent Git blob: `0482cf4c08b8c04d524a3eac11b798f07f0e0524`;
- candidate_v2 changes only occupancy implementation;
- bytes from `def analyze` through EOF are parent-identical, SHA-256 `d4d4e5c4cda6d94b1f1fa28a039d97a1c144338b8df1dd45e4727e636ba7347e`;
- exhaustive boundary corpus: **387,072** cases, mismatch0;
- malformed controls: **7**, exception type/message mismatch0;
- bounded random full-analyze comparison: **200,000**, output-or-exception mismatch0;
- raw-ns stress: **100,000**, occupancy oracle mismatch0, effect-bucket oracle mismatch0, invariant errors0;
- independent audit PASS/errors[];
- corruption controls **8/8**;
- RESULT SHA-256 `a72733e2fcd52adda46ed72f89d858b599ef800d7ab25146c688c729f44e9a30`.

Scoped conclusion: the #1328 interval-union occupancy helper integrates into the complete #988 analyzer without changing tested effect classification, validation or exception behavior. This removes the implementation boundary identified by #1325 without changing the causal-effect science contract.

This remains offline evidence. #1325 is not relabelled. A live successor must receive a fresh #60 lease and may change only the analyzer dependency from exact #988 v1 to this frozen candidate_v2.
