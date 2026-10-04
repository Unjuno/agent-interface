# Commands

Parent RED check (the modified regression file was copied into a detached worktree at the frozen parent; production source was unchanged):

```sh
python -m unittest \
  research.doom.test_doom_typed_release_backend_v3.Tests.test_malformed_owner_release_timestamp_fails_closed \
  research.doom.test_doom_typed_release_backend_v3.Tests.test_malformed_owner_record_fails_closed \
  research.doom.test_doom_typed_release_backend_v3.Tests.test_malformed_release_bracket_fails_closed
```

The same three RED tests were repeated against `90e65c932a8a487d9657713e5a243cba25125c4f`. PR #7399 subsequently added owner-history validation; the caller-bracket regression was run against its exact parent `f63f673538690fe6d6661a22d894cf1c061d3385`. See `results/RAW_7399_PARENT_RED.txt`, `results/RAW_7399_BACKEND_TESTS.txt`, and `results/RAW_7399_OWNER_TESTS.txt`.

Candidate checks:

```sh
python -m unittest research.doom.test_doom_typed_release_backend_v3
python -m unittest research.live_control.test_input_transition_owner_v3
python -m py_compile research/doom/doom_typed_release_backend_v3.py research/doom/test_doom_typed_release_backend_v3.py
git diff --check
python research/doom/map01-v39-release-cleanup-followup-v1/audit.py
python research/doom/map01-v39-release-cleanup-followup-v1/write_checksums.py
```
