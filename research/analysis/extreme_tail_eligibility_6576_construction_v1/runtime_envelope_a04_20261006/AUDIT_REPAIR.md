# A04 audit CLI repair and source-hash discrepancy

The exact `audit.py` bytes are unchanged from both the original source branch and this PR head (SHA-256 `69a21440bdb28d73cf764006350381b1222e5d458bb93fd547c0f220d17811a1`). The checked-in `SHA256SUMS.source` lists `8c426b37f9e8723ec1b715610a6f914e37a0f8951a5e9c2076f5c8b09ef20080` for `audit.py`, so that source manifest does not match the file on either ref. This discrepancy predates this repair and remains unresolved; the manifest hash is not presented as verified.

`audit_cli_repaired.py` is an additive copy of those exact bytes with only the malformed output newline literal repaired (SHA-256 `353df21fc419f8e4d9f5928e273a181c6fdb1457ff9a69e231f490424660f1ec`). Its syntax and `--help` path pass. The formal audit was not run because the original 2,925,419-byte `formal/RAW.jsonl` is absent from this GitHub subtree, as recorded in `RAW_PROVENANCE.md`. No candidate, stored outcome, or scientific conclusion was changed or regenerated.
