# Current-main qualification (2026-10-27)

The retained A01 result and its original 13-file SHA-256 manifest verify unchanged. Its freeze pins seven source Git blobs at `e627b8954ecfbdd90ccfe35a81441a00d88047c8`. Comparison with main `4039e993e585fef371a7fed75c42515a7eec9c50` finds one identical source blob (`research/live_control/input_transition_owner_v4.py`) and six changed source blobs:

- `research/doom/map01_overlap_controller_v39.py`
- `research/doom/session_map01_v15.py`
- `research/doom/doom_owner_thread_release_batch_backend_v1.py`
- `research/doom/doom_typed_release_backend_v2.py`
- `research/live_control/input_transition_owner_v3.py`
- `research/live_control/input_owner_v12.py`

The retained construction pass applies to its frozen source identities. The original README's reference to matching earlier main `674a0b3` is historical and does not establish the current dispatch chain. Before a new live allocation, freeze and independently verify the then-current source and chosen flags; do not infer the launch mode of a prior run from this construction. No live session, task effect, physical input, or model behavior was tested in this preservation.
