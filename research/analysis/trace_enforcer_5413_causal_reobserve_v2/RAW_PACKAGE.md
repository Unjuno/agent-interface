# Raw gzip transport package

GitHub's repository file reader is UTF-8 text-only, so the exact `raw.jsonl.gz` bytes are represented by 54 ASCII Base64 chunk files at `raw.jsonl.gz.b64.parts/part-000.b64` through `part-053.b64`.

Reconstruction: concatenate the chunk file contents in ascending numeric order with no separators; Base64-decode the resulting ASCII; write those decoded bytes as `raw.jsonl.gz`; then gzip-decompress to obtain the original UTF-8 JSONL.

Checks:

- Encoded concatenation: 1,498,932 ASCII bytes; SHA-256 `26f894ab3a1d8c430efd13de38f47ba923c362db59217d483932d814d8beaa05`.
- Decoded gzip: 1,124,199 bytes; SHA-256 `4161f7cae2d8a5d4d07b40cac185c031c5552464e24457ecc9436cfcfe382d1e`.
- Decompressed JSONL: 77,327,886 bytes; SHA-256 `d58259ada5635fdda3979a4aa66859a11456be68145a57af8fceffbc027e9e9b`.
- Expected records: 137,257.

The chunk representation is transport-only. It does not alter the runner output or raw bytes.
