# One-shot invocation record

Frozen source: [`FREEZE.json`](FREEZE.json). Base: `fabdb1de8273e8a87dfb2bea53856079da997998`.

| Role | Exact command | Count | Exit | Output SHA-256 |
|---|---|---:|---:|---|
| Candidate | `python3 research/analysis/crosslingual_visual_injection_7650_t0_a01_20261008/candidate.py` | 1 | 0 | stdout `5082635896de6c7137d17c4fad9e4260a8b99fbe15b76cf06ce442c9c2593f1b`; raw JSON `c11da4fd1f062127a13e253e35536440d0a9b08c45ef48a639843a5f7597ccc7` |
| Auditor | `python3 research/analysis/crosslingual_visual_injection_7650_t0_a01_20261008/audit.py research/analysis/crosslingual_visual_injection_7650_t0_a01_20261008/RAW.json` | 1 | 0 | stdout `4599ad8d1561f217f3184ea3b58a20c9bf37233a7f12f5ba861ea0a46580d07c` |

Stderr for both was empty (`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`). Formal retries: 0. `CANDIDATE.exit` and `AUDIT.exit` retain exit codes. A separate pre-freeze manifest-helper command had a syntax error before any formal auditor call; it did not alter candidate source or output and is disclosed here to keep the execution trail complete. The manifest was corrected before the sole auditor invocation.

The raw output is synthetic bookkeeping with placeholder flags only. It contains no English or Turkish linguistic stimulus, no screenshots and no pixels.
