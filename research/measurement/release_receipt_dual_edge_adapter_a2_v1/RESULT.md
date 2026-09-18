# #1425 exact-source release-receipt dual-edge adapter A2

Decision: `PASS_RELEASE_RECEIPT_DUAL_EDGE_ADAPTER_A2_SCOPED`.

This A2 changes only the predecessor #1362 harness source-identity factor. Before the primary block, the exact #988 `candidate.py` bytes were materialized and verified as Git blob `0482cf4c08b8c04d524a3eac11b798f07f0e0524`. Producer identities remained pinned to InputOwner v11 `842071284156d3ccc647f47135ee62a9e512cb56` and DOOM typed-release backend v2 `cf13d630ae22a50272a766c86d7f325f352a89d7`.

One frozen deterministic primary used seed 1362 and 250,000 source-shaped down/release pairs. It accepted 12,485 matched pairs. Candidate/oracle acceptance/reason mismatches, interval-transform mismatches, timestamp exactification, authority expansion, exact-#988 Actuation construction errors, and the bounded #988 analysis-subset mismatches were all zero. All 19 fixed mutation controls failed closed. Primary invocations=1; reruns/replacements/tuning=0.

The adapter preserves down `[admitted_ns,input_ack_ns]` and release `[call_started_ns,call_returned_ns]` exactly, requires exact `{id,step,owner_id,intent_token,key}` lineage, returns `grants_input_authority=false`, and emits only source-bound same-process clock provenance. It does not synthesize a row-level clock ID or either physical-edge instant.

Primary result SHA-256: `6b43daaeea6d2a7806d3e5cf8a3c73a57c4b826aae2995d4af1edb63c25e4644`.

Limits: this is offline integration evidence only. It does not locate a physical X11 edge inside either interval, prove application consumption, establish MAP01 usefulness/task correctness, human tempo, model/token savings, or a production ABI. A future producer process/clock split would require a new provenance proof.
