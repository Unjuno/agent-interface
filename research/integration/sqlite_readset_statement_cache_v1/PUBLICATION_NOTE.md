# Publication note — 2026-09-22

This directory retrospectively publishes the already-completed local allocation `sqlite-readset-cache-20260922-01` under Issue #4088.

The original experiment ran before this connection exposed GitHub write actions. Therefore the retained REPORT and bundle truthfully say that remote publication was blocked at execution time. **Do not edit or reinterpret that historical statement.** This note records only the later delivery step.

- Scientific allocation: one 60-case formal allocation, 10 fixed batches, reruns/replacements/post-freeze tuning 0.
- Retained decision: `PASS_SQLITE_READSET_CACHE_BOUNDARY_SCOPED`.
- Parent questions: #1713 and closed #501.
- Publication intake main: `2c76b9e41fd9757cba43dd1968ed71695d8e1fd0`.
- Publication branch: `research/sqlite-readset-cache-4088-20260922`.
- Original ZIP SHA-256: `1a573c0037b5d538183d5ccf2dc6a81d36e2a4a62c3314450672fbed8a5ed2e3`.
- Original ZIP size: 302,524 bytes.

The Base64 parts in `publication_parts/` concatenate to that exact ZIP. `unpack_publication.py` verifies every part hash, the decoded ZIP size/hash, and extracts only into a new destination.

Publication does not authorize a new formal run, production adoption, shared-runtime mutation, or closure of #1713/#57/#2789. The original construction failures, failed preliminary precision gate, raw SQLite databases, process exits, source freeze, auditor and corruption controls remain inside the immutable ZIP.
