# Raw evidence provenance

The executed formal candidate wrote one exact `formal/RAW.jsonl` file.

- bytes: 2,925,419
- SHA-256: `b5fe935cd03e00b32972353d9860071b9faabc9e038521f69a74512a6ea4f98a`
- rows: 90
- generator source: `candidate.py`, SHA-256 `c403b4750b4eaccfbc2d97b2b38dbe77611fac4e3460a0d410576ed97e44abd3`
- formal seeds: 65764101..65764130 under each of the three frozen conditions
- environment: CPython 3.13.5, Linux x86_64/glibc 2.41 in the provided execution container

The exact raw file is retained in the conversation-side lossless evidence archive, but it is **not falsely claimed as fully uploaded to this GitHub subtree**. Connector publication of the 360,664-byte compressed archive could not be completed with byte-verifiable transfer in this session; an attempted unverifiable fragment was deleted before PR creation.

`remote_raw_complete=false`.

Because this is a deterministic synthetic generator, the source, seeds and environment above specify a reproducible raw stream, and the published result/audit bind the executed raw by its SHA-256. Regeneration is reproduction evidence, not the original raw object and must not be relabelled as such.

This publication limitation does not change the local first outcome, but it remains an evidence-delivery limitation for reviewers deciding whether this PR is sufficient to merge.
