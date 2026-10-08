# Publication status — STOP_SOURCE_PUBLICATION_BLOCKED

- Issue: #4087
- Original experiment: `cache-stream-verification-4029-20260922-01`
- Scientific disposition: `PASS_STREAMING_REUSE_CONTRACT_SCOPED`
- Publication disposition: `STOP_SOURCE_PUBLICATION_BLOCKED`
- Branch base at creation: `5ffe12a426ab9852b79f2b34154650e6e91d1255`
- Original ZIP: 8,504,537 bytes, SHA-256 `5a321664e62dab7f8efd4490fea2a92954e176c627929a5667e4da43d50d035b`
- Original freeze SHA-256: `a49e0e746cfbb5bf657006a4c4d99aac1e498d27bef921641e28206fb1fef8ad`
- Original audit SHA-256: `d0f33cf29c6237f6cb175e4c1879d428c1e4b34bb3f3ca6512686c5ec02b1a94`

Exact Git-blob readback succeeded before the blocked operation for the source/plan files retained in this directory. The blocked call included `make_inputs.py`, `run_batch.py`, and `execute_batch.py`; no branch/tree ref was changed by it. A prior binary-patch staging attempt also failed exact Git-blob comparison before ref mutation because the Files text renderer did not preserve the binary patch byte stream.

No alternate endpoint was used to evade either block. No formal case was rerun. The missing source/raw bytes make this publication incomplete; keep the PR Draft and do not merge it as a complete research bundle.
