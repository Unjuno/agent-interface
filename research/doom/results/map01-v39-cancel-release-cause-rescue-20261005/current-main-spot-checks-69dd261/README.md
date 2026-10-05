# Current-main cancellation spot checks

One invocation each on current `main` `69dd261430cb1ed875f5a76411c4a2a54777c114` with host Python 3.12.13. Both tests use deterministic fake-Xlib interleavings; no container, X server, game, GUI, model, device, or formal allocation was used.

- `python -B research/live_control/test_executor_owner_cancel_cause_postsample_v1.py`: PASS 1/1; cancelled release receipt precedes the cancelled terminal event.
- `python -B research/live_control/test_executor_owner_cancel_cause_v1.py`: PASS 1/1.

`RUN.json` binds commands, test and output hashes, exit codes, and scope. These spot checks supplement but do not replace pull-request CI or establish live-control efficacy.
