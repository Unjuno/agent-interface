# A07 freeze — candidate invocation has not occurred as of freeze

Fresh successor to A06 `STOP_OUTPUT_PERMISSIONS`; A06 remains unchanged. No A06 input is reused. The new output-ownership protocol was tested before this freeze using separate disposable output mounts: the pinned R and Python images each created and hashed a zero-byte sentinel successfully as the default container root user. Candidate source parse/import and package checks passed; no fit or audit was invoked in preflight.

## Source/input identity

- Base commit: `b711b7781cabcf23d40d078c376ffad52bd33201`.
- Frozen `tailid_equivalent.py` SHA-256 `1931b354fedb3db2a5cda9c52cdd4c1e9002bb04dbe952980704c282777a63c4`.
- `PREREGISTRATION.md` `8089f3d0320b8fc502ae31856b85b990e0a84131d588bd118df4e7a9bc49d9d6`.
- `prereg.json` `74a96ee30c80dfb421a409beb1ef669074225ae5544952e25261336cdeb0b039`.
- `generate.R` `a7c46b0af900069d932c6e910d31b306aed38b29bdf14f4866fe45b35175851e`.
- `candidate_r.R` `7bd4b4ee1b770e7aef663ab782ae5c05b16cc03482666bee86ad5c8e0ce309b8`.
- `candidate_python.py` `fa7cfa07e5bf198d00ac2322817486350682d3503f5c8312f7169b827829d634`.
- `audit.py` `298ff1aee21ebadfeca2ad8e5d405c6b01986b9c4f0272448e66b201d15fbbde`.

Frozen fresh-input hashes:

| Seed | SHA-256 |
|---:|---|
| 65769937 | `9dc23f2962c2f80107884ce530b9bdc464053587452b7d5f346b253b5fc7cf50` |
| 65769938 | `1637fb6ac5a831e07c7b628379573e45a3757444db7d7594a0b75d2951e5e78e` |
| 65769939 | `b85c9e629fd51896cb170728d6c202131afa7e4196e11512bc17cf29e84b611e` |
| 65769940 | `8e0cff8f7384b03fa3bac302bbec0fb1170edacb475fa239be78f3569c8e5037` |
| 65769941 | `1e0e7ceecb59b56cf229cf6f79ebe1fd97a8f5e628471eee46bac5855b234a9d` |
| 65769942 | `57e76d24285ba99bb9a406b82aca71a8ad07b87911a914b9e0f2fa91c29a1fbc` |

## OrbStack and execution envelope

- Dedicated VM `agent-interface-6576-tailid-parity-a03-20261002`, ID `01M3Y3Z0A534XSFW13KW95E98Y`, Ubuntu 24.04.5 arm64, 2 CPU / 4 GiB.
- Private Docker Engine `2cc9fcfe-a017-4956-959f-0b1a85657dde`, version 29.1.3; outer cgroups observed CPU quota 2 cores, memory 4 GiB, swap 0.
- R image `local/6576-cran-parity-a03:r-only`, ID `sha256:bff4bd37d7c0cdce60330ffd8e517ea0e7ba2dc0ecb50bfec65954bafcb33559`, R 4.4.3, ismev 1.43, jsonlite 2.0.0.
- Python image `python:3.12-slim`, digest `sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`, CPython 3.12.15 linux/arm64.
- Candidate root filesystem read-only; no network; prereg/source/input mounts read-only; independent writable output mounts. Default container root identity is deliberate and prevalidated against separate disposable mounts to avoid A06's UID 1000 versus VM UID 501 mismatch. Limits: 1 CPU, 2 GiB memory, `memory-swap=2 GiB` (no swap), `/tmp` tmpfs only.
- R and Python candidate containers will be inspected before first start; start each once. Run the separate raw-only auditor once only if both candidates exit 0. Retries and post-invocation repairs are zero.

No shared OrbStack Docker Engine, other VM, formal six-case T0 allocation, physical input, or GUI is used. Any A07 failure is retained without rerun.
