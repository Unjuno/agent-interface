# STOP report — #4767 diagnostic construction

## Disposition

`STOP_AUDIT_AND_PROVENANCE_DEFECT`. The local Docker process completed one
paired CPU training orchestration on seed 7866101, but an independent raw-only
auditor rejected the retained record because its asserted support-prefix
control is false. Do not interpret the observed accuracy difference as a
scientific result. Do not rerun this seed or repair its raw output in place.

The runner was independently transcribed from the visible #4749 contract and
the retained #3890 `source/runner.py`; however, the #4749 repository directory
lists `formal.py`, `support_formal_builder.py`, and `support_loader.py` at its
root, while fetches for the latter two returned 404. The directory README says
ten offline tests pass, but its published directory listing has no `tests/`
directory. The exact formal builder / loader binding therefore cannot be
verified from the public main snapshot used here. The raw `support16_is_prefix`
field also came from an erroneous check against the full 64-row tensor rather
than a regenerated 16-row stream. This record is retained as a failed
construction/audit event, not as an efficacy observation.

## Immutable local raw and audit

- `RAW.json` SHA-256: `e82cbd35e46a1fcc66e906a6c58a30149e64bcc4d5afbfb15fd92e9247bf5212`
- Raw payload self-hash (as emitted): `e24eb708ab5de7d1c3beaafa8ac2fba795c46ccf35e447dd82184438134ae9dc`
- Runner source at execution SHA-256: `e33e7be82cf00bbc7fe8f44462382d92fc6729e0c71c505efeb3972af72406f4`
- Raw-only audit source SHA-256: `c6bc73d3f3eca911fd6b403010e64f3387e70ecf5062fdfbb6fabec3894d18ef`
- Independent audit: `HOLD_RAW_RECORD`, error `support_prefix`; the audit
  additionally records that training-source replay, Docker invocation binding,
  and prefix truth from omitted raw inputs were not verified.
- The displayed delta `+0.027587890625` is not accepted as evidence and is
  intentionally not interpreted.

## Environment and command

- Host: Windows x86_64, Docker Desktop Linux engine; local inventory showed
  Intel i7-12700H, approximately 31.7 GiB RAM, NVIDIA RTX 3080 Laptop 16 GiB.
- Container: `needle-pilot05:local`, immutable ID
  `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`,
  linux/amd64, Python 3.12.14, PyTorch 2.5.1+cpu, one CPU thread; warning that
  NumPy is absent. No GPU was used.
- Invocation: `docker run --rm --pull=never --platform linux/amd64 --network
  none --read-only --cpus=1 --memory=2g --pids-limit=64
  --security-opt=no-new-privileges --tmpfs
  /tmp:rw,nosuid,nodev,size=64m ... needle-pilot05:local -B
  /src/diagnostic.py`.
- No retry, network, package install, provider/model API, GUI, user data, or
  action authority.

The sole authorized follow-up is to resolve the source/provenance discrepancy
and, if scientifically useful, create a new independently frozen diagnostic
allocation with a new seed and complete source/pairing tests. This STOP does
not consume or modify #4749's reserved formal seeds.