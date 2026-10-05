# MAP01 V39 Xvfb per-key release identity A04

A04 follows A03's retained trace `STOP` (`AttributeError: detail`, zero observed client edges, clean Xvfb exit). It fixes the harness to retain and skip non-key X protocol notifications while waiting for the expected key edge, retains any partial receipts immediately, and never reruns or replaces A03.

Read `PREREGISTRATION.md` and verify `FREEZE.json` and `SHA256SUMS` before the one candidate invocation. The local test command is:

```sh
wsl -e bash -lc 'cd /mnt/c/Users/junny/Documents/Codex/2026-10-03/new-chat-3/work/agent-interface-v39-perkey-a03 && python3 -B research/doom/map01_v39_xvfb_per_key_release_identity_a04_20261005/SOURCE/candidate.py --out research/doom/map01_v39_xvfb_per_key_release_identity_a04_20261005/results/A04 --display :126'
```

If raw output exists, run the frozen raw-only auditor once. This A04 synthetic qualification does not run Doom or use Issue #59's unassigned private game lane.
