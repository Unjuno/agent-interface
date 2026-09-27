# Frozen input and raw evidence reconstruction

## Schedule input

Concatenate all `input/schedule.json.gz.b64.part-NNN` files in ascending
numeric order with no inserted whitespace, Base64-decode the result, verify
gzip SHA-256 `324e8690cad622efffd8a81bbcdc0ccf25944f8d3254e76a5774becb6998dcf8`,
and decompress. The exact schedule JSON is 262,252 bytes with SHA-256
`f778860219a8a9ffe8014eb00eeb41456dac1bf58a2687ee64045a2b9e1df733`.
Regeneration from the frozen `src/generate_schedule.py` must produce the same
bytes.

## Raw result

The original raw evidence was `raw.json` (1,688,320 bytes; SHA-256
`d0284b83b4a4c2f5c8efe1c3a9411bd2c5fd99ca97e0e9761f9c6e820f328228`). Its
lossless gzip is 119,128 bytes with SHA-256
`091d382eb4f6102a5991791405d65be58a422abfaf04f2b0e1e8b7a075261b38`.

To reconstruct, concatenate all `formal/raw.json.gz.b64.part-NNN` files in
ascending numeric order with no inserted whitespace, Base64-decode the result,
verify the gzip SHA-256 above, decompress, then verify the raw byte count and
SHA-256 above. The resulting UTF-8 JSON contains all 225 complete worker
stdout records, including each full selected-ID trace, plus captured stderr,
exit status and wrapper elapsed time.
