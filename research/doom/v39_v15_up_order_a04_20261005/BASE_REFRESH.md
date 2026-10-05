# A04 evidence refresh onto current main

The experiment was preregistered and executed against source commit `69dd261430cb1ed875f5a76411c4a2a54777c114`. For review delivery, this additive evidence package was copied onto a branch created from main commit `e7c916989da30741b00c234efd264067d0899851`; the experiment was not rerun and its original raw/audit bytes are retained.

At refresh, all five executable source Git blob IDs were rechecked against current main and remained identical to the frozen source IDs in `FREEZE.json`:

- `input_owner_v10.py`: `341b3c01649943ddaad5f28431a792c4889cc36e`
- `input_owner_v12.py`: `3addfe06a9d5116ec3b3d42b2ffe139885872adc`
- `input_transition_owner_v3.py`: `7d990a654804ba3ed7d406baee40c31b6cb27375`
- `input_transition_owner_v4.py`: `02c23c34e9382650a46e80d75fe49d5409153b75`
- `doom_owner_thread_release_batch_backend_v1.py`: `f249ef036a9ec56740961af4aee375a28d9e133f`

The branch is delivery-only: it adds the self-contained protocol, frozen candidate/auditor/runner, source snapshots, raw trace, independent audit, result, and hash manifests. No production code or default runtime behavior changes.
