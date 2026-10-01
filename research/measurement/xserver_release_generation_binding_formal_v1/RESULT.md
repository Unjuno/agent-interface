# Fresh formal result — X-server cleanup generation binding

Decision: **PASS_RELEASE_CONFIRMATION_GENERATION_BINDING_FORMAL_SCOPED**

One formal invocation, reruns0, seed `112420260918202`.

Random stratum: 400,000 traces / 1,801,437 events. Candidate-oracle mismatch0; retro-confirmation escapes0; terminal mutations0; false exact-lineage rejections0; exact same-generation confirmations104,037; backend-loss terminals103,576.

Exhaustive event-language stratum: 3,906 traces /18,555 events. Mismatch0; retro0; terminal mutations0; false exact rejection0; exact confirmations1,771; backend-loss terminals1,771.

Malformed controls:9/9 fail closed. Candidate parent Git blob before/after is exact `b19a76f1024a507918cb2c23d6f7e70d247700b6`. Authority grants0; task-input grants0.

Independent audit recomputed all aggregate fields from the normalized per-trace ledger and passed with errors[]. Corruption controls4/4 were detected.

Retention note: the local full normalized CSV ledger is 15,294,020 bytes (SHA-256 `0ab02cff...`) and its gzip is SHA-256 `fef9cc11...`. Git retains a lossless sufficient-statistic normalization (`NORMALIZED_LEDGER_COUNTS.json.gz.b64`) whose decoded JSON reproduces every audited aggregate; `RETENTION_AUDIT.json` proves that reconstruction. The released collision worker's `source.part*` package remains noncanonical and is not pooled.

Scope: this validates the typed release-confirmation generation barrier only. It does not prove live X11 reconnect behavior or production generation-token minting.
