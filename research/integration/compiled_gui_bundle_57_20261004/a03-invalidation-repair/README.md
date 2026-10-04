# A03: invalidation and bounded repair composition

Issue #57 test-double integration extension. It tests the adaptive caller's cached-target invalidation -> repair -> final revalidation -> compiled GUI graph route on current main and the PR #7330 composition candidate.

Cases: (1) no-authority local repair, followed by two compiled transitions; (2) one charged model reacquisition, exact post-model/current-observation receipt check, final revalidation and two compiled transitions; (3) association change at the post-model check, which stops before execute and effect verification. Exact caller and compiled source hashes are embedded in each raw run. The updated candidate is PR #7330 head `ed326ccfeae1c66fde4ec38d0d3dcd9b54ca53d0` (caller SHA-256 `e9be73955d849a8d627450752a4b6b97a410cdd08e9424746d954e23015a654d`).

Run against each source checkout:

```sh
PYTHONPATH=research/live_control:. python3 -B research/integration/compiled_gui_bundle_57_20261004/a03-invalidation-repair/run.py /tmp/RUN.json
```

The saved-only auditor checks both outputs and verifies the three boundaries. Results and `AUDIT.json` are retained in this folder. The model usage/wait are test fixtures. This does not exercise a live cache, target handle, provider, screen or physical input, and says nothing about repair cost or efficiency.
