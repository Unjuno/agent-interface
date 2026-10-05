# Checkout line-ending custody note

The formal run used Windows text output with CRLF line endings. `RUN.json`
records the byte counts and SHA-256 digests of those raw outputs. Git initially
normalized their line endings to LF on commit, so the committed copies did not
match those recorded raw digests even though their parsed content did.

This follow-up restores the exact CRLF byte sequences from the retained Git
content and verifies each against the frozen `RUN.json` byte count and digest.
The package-local attributes keep all source and documentation at LF while
preserving `raw/` bytes exactly. Neither candidate nor auditor was rerun; no
semantic content was regenerated. `SHA256SUMS` covers the exact preserved raw
bytes and all other tracked package files except itself.
