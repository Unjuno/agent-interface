# Result — #1304 dual-root effect authenticity

Decision: **PASS_EFFECT_DUAL_ROOT_SINGLE_COMPROMISE_SCOPED**.

- 240,000 traces = 4 immutable batches × 60,000.
- Candidate / independent oracle mismatches: 0.
- Dual-root false SELF effect credit: 0.
- Replay escape: 0.
- Scorer-only baseline false SELF effect credit under scorer-key compromise: 72,000.
- Authority promotions: 0.
- Batch reruns/replacements/tuning: 0.
- RESULT SHA-256: `e22bd5a4a0c5b340d73e8ddbd536ca9533fb14d4cda79d77534b34ce72d4c9ea`.
- Batch concat SHA-256: `4da1e8882594f210738741f5ee63396fd7639b0d9f688d10e063f0f8e760e528`.

Scoped conclusion: under the frozen condition where only the scorer key is compromised and the application/effect root remains independent, requiring 2-of-2 signatures over identical effect receipt bytes closes the tested single-root forgery paths. This does not protect against compromise of both roots or establish operational key independence in a live application.
