# A02 formal run and adjudication

Allocation: `HISTORY-RECEIPT-PROVENANCE-6616-A02-20261003`

Base: `9a327d0511f02c7b8ebd175e20f96a43028578ca`

Frozen commit at allocation time: `be501da33`
Runtime: OrbStack private Docker Engine in VM `agent-interface-6576-tailid-parity-a03-20261002`; pinned `python:3.12-slim@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016` (`linux/arm64`), network none, read-only root and source, 1 CPU, 256 MiB requested, 64 PIDs, all capabilities dropped, no-new-privileges. Both containers exited 0 and `OOMKilled=false`; effective memory enforcement is not claimed.

## Formal counts and outcome

- Candidate: 1/1, exit 0, container ID `7d373303f791009b286f742fee708bf8d111043efa2629643a62bbb3cdc34554`.
- Independent auditor: 1/1, exit 0, container ID `97321edfb3d08ce4a382d5630e71324c43b361b4ca23fbdcbffba6f96396e53c`.
- Retries: 0. Audit reconstructed 5/5 rows with `errors=[]` and emitted `PASS_METHOD_SCOPED` for the fixture's lifecycle classifications.
- Candidate raw SHA-256: `409bbb1ccf6a74608135ca9aa1e86dc810731e2b3cd46fec1c4e98f521025c04`.
- Audit JSON SHA-256: `01cc70a4ec3333517c05b231323c92bf2b409f23a817a3f5bb2ff8649c0c68bc`.

## Post-run adjudication

The fixture embeds allocation ID `HISTORY-RECEIPT-PROVENANCE-6616-A01-20261002`, but A02's freeze declares `HISTORY-RECEIPT-PROVENANCE-6616-A02-20261003`. Candidate and auditor agree with each other because both treat the fixture's ID as authoritative; neither binds it to the freeze. Therefore the fixture-level method output is retained, but the allocation-level disposition is **`HOLD_ALLOCATION_ID_MISMATCH`**, not PASS. This exposes a preregistration/source-binding gap. No repair or rerun was performed. The hold applies to allocation binding; it does not invalidate the raw classification rows as descriptive output.

The intended post-transfer hash gate passed for all three formal input files before launch. Construction tests: 4/4; `py_compile`: pass. A01's prior `STOP_CONTAINER_SOURCE_MOUNT_EMPTY` remains in its separate directory and was not modified beyond adding its STOP record.

No GUI, human, participant, model, user files, network, or external side effects were involved. This establishes no actual user reliance, authentic host-process provenance, or production assurance.

## Commands

Candidate:

```text
docker run --name 6616-a02-candidate --network none --cpus 1 --memory 256m --pids-limit 64 --read-only --cap-drop ALL --security-opt no-new-privileges --mount type=bind,src=/home/taka/6616-a02,dst=/src,readonly --mount type=bind,src=/root/6616-a02/out,dst=/out --workdir /src python:3.12-slim@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016 python /src/candidate.py /src/fixture.json /out/candidate.json
```

Auditor used the same image and isolation settings in a separate container, invoking `/src/audit.py /src/fixture.json /out/candidate.json /out/audit.json` against the candidate's retained raw output.
