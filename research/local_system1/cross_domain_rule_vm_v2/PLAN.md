# Cross-domain typed rule VM v2

Harness-only successor to #934 STOPPED_FORMAL_HARNESS_ADAPTER_HASH. Scientific VM, exact #900 decision source, fixture, retained evidence, corpus, timing schedule and gates are unchanged. Only post-timing output canonicalization is repaired so diagnostic `Request` values can be hashed after the timed region.

Formal: 8192 unique Chromium payloads; five exact retained OpenTTD states; four structural fail-closed controls; 1024 warmups + 65536 batch-1 timed calls per arm/domain; one fresh formal invocation; reruns/tuning/replacements 0.
