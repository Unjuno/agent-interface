# Construction-only checks — Issue #4619

Construction may import the frozen modules and execute unit tests but must never call the optimizer, `runner.main`, or the host `formal.main` orchestration. The mocked missing-environment test asserts STOP before `train`; command tests require exact `NEEDLE_SEED` and `NEEDLE_OUTPUT=/out` Docker arguments and unique seed output mounts. Seed-stream tests prove all new base/data/update offsets are disjoint from known predecessor and STOP schedules. Additional tests cover deterministic labels/data and schema/digest refusal.

Pinned image: `needle-pilot05:local`, image ID `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`. Container command is network-none, read-only root and source, dedicated writable /tmp tmpfs; no package installs. Preserve construction results separately from the sole formal training allocation.
