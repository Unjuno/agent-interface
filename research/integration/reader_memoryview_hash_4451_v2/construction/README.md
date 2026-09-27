# Preformal construction artifact

This is excluded construction evidence for the source freeze in the parent directory. It is not a formal allocation. The verified local Docker image is `sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419` (Linux/amd64, CPython 3.13.5); formal invocation count remains zero.

`preflight-evidence.zip` SHA-256: `16dc1b3f16bf17c085ef0f54727b683e24aa973d9739eccc3ae358a4cdfdcf11`

The archive contains the corpus, invocation manifest, durable worker JSONL, fsync journal, run summary, independent audit, ten corruption-control results, and injected-timeout result. Archive decompression was verified byte-for-byte against each retained local file.

| File | Bytes | SHA-256 |
|---|---:|---|
| `AUDIT.json` | 129 | `dbe31e5c67d3a555c092f7539a725d2d1ecb565b6a841311073909bc1eb11856` |
| `corpus.jsonl` | 16,384 | `19ab1521eeeecbdd57dc89211112bf0b45b58533dca070d6fa352729734c1125` |
| `CORRUPTIONS.json` | 2,110 | `1123875d0a144096a87090eae054b4fb592b0ac4b489d444de65dbe5aeaf9baa` |
| `DURABILITY.json` | 167 | `218e1f7af2854efe22b97e190cf9094801dce3e483f372254b6aac2d66f42eea` |
| `INVOCATION.json` | 1,057 | `3899b4e78fb3c40768df3f6945470aa1d996e6da607ce227977fa3f99d1bfb5b` |
| `journal.jsonl` | 6,660 | `f7ba30832c7ec1c9f89a7940bd6156994aa0a57c3bfc3f8c41413650952f3fa5` |
| `RAW.json` | 54,714 | `1f999dfa9bdcca6f7da298c92a16e0b60abfee584b7914dc458d680e1a49e943` |
| `RAW.jsonl` | 53,666 | `b54f2b15c99110022aa4882b63b43d092200c24389151040a80e5985636a294d` |

Audit disposition: `PASS_CONSTRUCTION` (40 checks, `errors=[]`). Ten copied-evidence mutations all produced structured audit failures with nonempty errors and empty stderr. The timeout control produced paired durable start/completion records and `STOP_WORKER_TIMEOUT`. Earlier preformal harness defects and the source-mount STOP are documented in the parent `CONSTRUCTION.md`; none started a formal worker.
