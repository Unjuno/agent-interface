# A14 run record

- Three local CPython invocations total: the first and second both failed only the positive-control fixture because it did not publish a fresh sequence-11 observation during the pending wait; the second was inadvertently repeated after a failed source replacement. Both first outcomes are retained here. After correcting the fixture to publish sequence 11 in both arms, the final local preflight passed 2/2.
- Final frozen WSLc 3.0.1.0 run: one invocation; Python 3.14.8; 2/2 passed; exit 0; image `sha256:3e93e42958f7e4b1525a638c2388fc67419dc59eeb1d70334b0c17d80bcf8782`.
- Requested limits: `--network none --cpus 1 --memory 512m`. Runtime warned that swap-limit capabilities are unavailable; memory was limited without swap. No cgroup probe or enforcement claim.
- Both prompts use source ammo 6. During the pending adapter wait, the fake client publishes sequence 11. Current ammo 4 rejects the synthetic `minimum_ammo=5` action; unchanged ammo 6 reaches executor-ready only. Neither receipt has executor admission or input authority.
- This is construction evidence with a fake client and synthetic answer; it is not model or live-control evidence.
