# Post-hoc audit integrity result

Allocation: `target-belief-audit-4150-posthoc-01` (Issue #4609). This diagnostic audits retained ID003 evidence; it is not a new formal experiment and adds zero formal invocations or rows.

The frozen 64-row result passes the frozen auditor with zero errors. The independent per-row comparator check finds zero baseline mismatches. In a copied result, six valid ambiguous rows (r24, r25, r32, r33, r40, r41) were changed from ALLOW to REJECT, and six invalid-provenance rows (r02-r07) from REJECT to ALLOW, with companion fields updated consistently. The aggregate top1 false-ALLOW count remains 6. The frozen auditor still returns PASS with no errors, while an independent implementation identifies all 12 changed rows.

The original formal result SHA-256 is unchanged before and after: `6a391d2496c82282c66446213fdfc46e437baa512e4100697bc431a307a5d490`. The copied result hash is `fef6d5d5a10a3dae5fdb791157024c6b22d14c24737689dd6ad7d004ec604037`. The frozen audit source hash is `47ed66b5b5d3ae0d08453fe5f084b554e5f8311b35b16694a62079666898a9dd`; the diagnostic source hash is `c917f980a7823f81ad98cd99fe8330a19427ee217730468f839c25b19b9215fb`.

The one post-freeze diagnostic ran in the pinned local Linux/amd64 Docker image `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, with network disabled, read-only root and evidence mount, tmpfs output, 1 CPU, 512 MiB, and 32 PIDs. Full structured output is retained in [POSTHOC_DIAGNOSTIC.json](POSTHOC_DIAGNOSTIC.json). No GPU was used because this is a finite JSON/auditor mutation check.

Interpretation: ID003's retained rows are consistent with its frozen comparator and its scoped PASS remains unchanged. The demonstrated defect is specifically that its audit checks the comparator's aggregate false-ALLOW count but not each retained comparator decision, so this mutation class is invisible to that audit. This result does not estimate live detector quality or generalize to other mutation classes.
