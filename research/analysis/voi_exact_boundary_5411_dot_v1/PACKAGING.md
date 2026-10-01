# Lossless transport for the two larger evidence files

The scientific run and its 28-file logical package are unchanged. To avoid a large inline GitHub write, only evidence-01/EXACT_ROWS.jsonl and evidence-01/RESULT.json are stored in EVIDENCE_JSON.zip.b64. All other original files remain direct files at their original relative paths.

Decode the base64 as a ZIP and restore exactly the two relative member paths listed in TRANSPORT_MANIFEST.json beneath this study directory. Verify the compressed ZIP SHA-256 and both uncompressed sizes/hashes before use. The archive contains data only; no checker, predecessor, or consumed allocation needs to run. Reject any other member name or extraction outside this directory.

The original PACKAGE_MANIFEST.json and evidence-01/SHA256.json retain the original uncompressed identities. Their complete logical closure is checked after restoration; they do not claim that the two JSON data files are separate Git objects in this transport layout. Nothing was normalized, rerun, relabeled, or removed from the retained first outcome.

This packaging was prepared after the original create_tree publication was cancelled. The user approved publication resumption on 2026-09-30. The cancelled operation did not produce a confirmed evidence commit or PR. These three transport files are publication metadata, not additional scientific observations.
