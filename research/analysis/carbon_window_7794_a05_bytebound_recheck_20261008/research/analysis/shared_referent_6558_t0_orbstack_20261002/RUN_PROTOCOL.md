# Frozen one-shot T0 protocol

Allocation: `SHARED-REFERENT-6558-T0-ORBSTACK-20261002-01`.

1. Freeze source commit, input hashes, image digest, commands, gates and this protocol before formal invocation.
2. Run construction suite once before freeze; it must pass. Construction exercises functions/auditor mutation tests locally only and is not candidate/auditor formal evidence.
3. Run candidate CLI exactly once in an offline container. It reads only `fixtures.json`, writes a fresh raw output directory, and cannot read `oracle.json`.
4. Only if candidate exits 0 and emits the expected 9 rows, run independent auditor CLI exactly once in a distinct offline container. Mount fixture, oracle, and candidate raw read-only; only audit output is writable.
5. Preserve first exit status/raw. No repair, retry, rerun, or outcome relabel. Any launch failure after formal invocation begins is STOP; do not run the next stage.
6. Remove only the two newly created stopped containers after recording inspect state and mount identities. Never touch `unjuno-native-ci-6092`.

Image: `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` (present locally at preregistration).

Candidate command (package mounted read-only at `/src`, fresh writable candidate directory at `/out`):

```sh
python -B /src/candidate.py /src/fixtures.json /out/candidate.json
```

Independent auditor command (package mounted read-only at `/src`, candidate raw mounted read-only at `/raw`, fresh writable audit directory at `/out`):

```sh
python -B /src/auditor.py /src/fixtures.json /src/oracle.json /raw/candidate.json /out/audit.json
```

Both containers use `--network none --read-only`, a bounded `/tmp` tmpfs, explicit bind mounts, and no external effect. The candidate never receives the oracle. Formal attempt counts are fixed at construction=1 pre-freeze, candidate≤1, independent auditor≤1, retries=0.

Decision gates: all nine case IDs exactly once; baseline arm outputs independently reconstructed; three valid changed-generation cases re-ground to the hidden oracle target; two invalid-receipt controls return UNKNOWN; stable/zoom-only rows incur no re-ask; attention-only never grants authority; raw SHA in auditor report matches the candidate raw; four mutation checks reject target substitution, authority laundering, missing row, and invalid/stale receipt. No metric establishes participant or real-application behavior.
