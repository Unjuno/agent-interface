# Pre-freeze construction failure record

The first candidate invocation failed before producing a raw file. Docker traceback: `TypeError: unsupported operand type(s) for +: 'int' and 'list'` while aggregating nested canary-response arrays. The source was corrected to sum each binary attempt; the auditor received the corresponding independent flattening logic. This was pre-freeze construction work, not a scientific FAIL or formal allocation.

After that correction, a construction generation/audit produced 21 groups and `PASS_METHOD_SCOPED`; its outputs are retained unchanged as `construction_raw.jsonl` (SHA-256 `0cbd75a36215eda262ec1609e25d905d8816e3392e050d210120a6681d688bb6`) and `construction_audit.json` (SHA-256 `4bfabc994c428cb00009d74d6e6e79f150abaf664885db16126dd51bde622453`). The prospective freeze was then written, and the official run is separate.
