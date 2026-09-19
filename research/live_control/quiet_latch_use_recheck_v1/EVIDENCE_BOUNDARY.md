# Evidence boundary and reconstruction notes

Task: `QUIET-LATCH-USE-RECHECK-20260916-010`
Issue: #249
Frozen publication base: `0a9156e7c0931b086f5276e79873cf9fe03382eb`.

GitHub-retained readable evidence in this directory includes the report, aggregate audit, core candidate/source implementation, and this boundary record. The measured preregistration was frozen before execution and is SHA-256 `500af509a3889009aa700a78c86eb0c342490dc0054aaead68f6239eb7431add`; its exact schedule/hashes/gates are also recorded before measurement in Issue #249 and successor-freeze comment 5687209663.

The complete local lossless archive contains 658 package-manifest-bound files: final 56-case allocation, stopped 009 evidence, construction failures, exact measured sources, preregistrations, SQLite DBs, rendered-pixel payloads, logs and audit. Archive: 171,788 bytes, SHA-256 `d7323e8371ae99688d0e2e61e7d5489698e0f102874f4c08c4bb36e65e47d001`.

That full binary archive is **not claimed retained on GitHub in this commit** because the available MCP contents path accepts UTF-8 text rather than a local binary-file parameter. Do not substitute the aggregate audit for the full raw archive. The archive is retained as a conversation artifact and can be reconstructed/audited locally.

Final aggregate audit SHA-256: `dc3f14f92a795755e4615cb7c66ee720a240d413d8e8ba1c31a345a3cf822deb`.
Report SHA-256: `eb0c477780f63ff3730fb37d17c5c045c99fd87d775fd3b2213360f0545a1de3`.
Core source SHA-256s at freeze are listed in Issue #249. `version_view.py` and `source.py` are retained here verbatim; remaining exact source bytes remain in the local lossless archive and are hash-bound by the preregistration.

Fresh-directory local reconstruction reproduced the audit byte-for-byte: reconstructed audit SHA-256 equals `dc3f14f92a795755e4615cb7c66ee720a240d413d8e8ba1c31a345a3cf822deb`.
