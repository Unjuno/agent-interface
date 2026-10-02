# A08 freeze — candidates/auditor not yet invoked

Fresh-seed successor to A07's one-shot auditor STOP. All hypothesis, criteria, variants and failure semantics are in `PREREGISTRATION.md` and `prereg.json`. Candidate programs are byte-identical to A07; the independent auditor is new and explicitly treats failed starts as recorded outcomes while measuring only converged fits. New R-generated inputs use seeds 65769943–65769948; no A06/A07 input or output is reused.

## Immutable source/input identities

- Base source commit: `b711b7781cabcf23d40d078c376ffad52bd33201`.
- Frozen Python TailID equivalent SHA-256: `1931b354fedb3db2a5cda9c52cdd4c1e9002bb04dbe952980704c282777a63c4`.
- `PREREGISTRATION.md`: `4df0202609ac4717b98f65df24750085ae4f1744bf08a008bed4fae4bf4f58fd`.
- `prereg.json`: `822850afe55829216ad4d9b6795d3058a25740e3675721095bccdebc1f3044c5`.
- `generate.R`: `a7c46b0af900069d932c6e910d31b306aed38b29bdf14f4866fe45b35175851e`.
- `candidate_r.R`: `7bd4b4ee1b770e7aef663ab782ae5c05b16cc03482666bee86ad5c8e0ce309b8`.
- `candidate_python.py`: `fa7cfa07e5bf198d00ac2322817486350682d3503f5c8312f7169b827829d634`.
- `audit.py`: `50ecb6753fb1494f381ea6da63073d1f72a4d408baa924b4fd762ffd78668d74`.

| Seed | Frozen input SHA-256 |
|---:|---|
| 65769943 | `82e22bd02977b9f9ae46d05b4774559c9d3aacc1df7c525bf7dbba3811700048` |
| 65769944 | `8d218084bfd870c88886d742e85d48f978f265be8c9d0b7b9deba9c6794f83e1` |
| 65769945 | `744bd0c80415ce22fe194cab081e9511332d2b9da9458b98f75c9f19fa47e7a7` |
| 65769946 | `b5c12af27c741d2e5f54cf8c00957ca6ddaf26e615dc5c406a8f3fbffd15a076` |
| 65769947 | `3f519e9c3b5aea31df273ede8ebb360ec7aa0d3979cc3fcc01e6e90d002d2faf` |
| 65769948 | `4210cb83c3828f967dd91790b92ae8344bfa35b25fdf237a2880685b664f3044` |

## OrbStack/container environment

- Dedicated #6576 VM `agent-interface-6576-tailid-parity-a03-20261002`, ID `01M3Y3Z0A534XSFW13KW95E98Y`, Ubuntu 24.04.5 arm64, 2 CPU / 4 GiB.
- Private Docker Engine `2cc9fcfe-a017-4956-959f-0b1a85657dde`, 29.1.3; outer cgroup 2 CPU, 4 GiB RAM, no swap.
- R image `local/6576-cran-parity-a03:r-only`, ID `sha256:bff4bd37d7c0cdce60330ffd8e517ea0e7ba2dc0ecb50bfec65954bafcb33559` (R 4.4.3, ismev 1.43, jsonlite 2.0.0).
- Python image `python:3.12-slim`, digest `sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016` (CPython 3.12.15, linux/arm64).
- Before this freeze, separate disposable output mounts were successfully write-probed by each image using default container root. Candidate/auditor mounts are read-only except their distinct writable outputs. Root FS read-only, network none, 1 CPU, memory 2 GiB, memory-swap 2 GiB (zero swap), `/tmp` tmpfs. Source parse/import/version checks passed; no fitting or audit calculations occurred.
- Before any start, inspect that each candidate and auditor has the pinned image, network none, read-only root/source/input, separate outputs, and resource limits. Candidate invocations R=1/Python=1; auditor at most 1 only if both candidate exit codes are 0. Retries=0.

A08 is a synthetic method experiment only, separate from the formal six-case #6576 T0 and any physical-release evidence. Do not patch or rerun after an invocation.
