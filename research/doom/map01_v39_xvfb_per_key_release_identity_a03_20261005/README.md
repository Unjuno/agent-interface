# MAP01 V39 Xvfb per-key release identity A03

A03 is a new allocation after A02's retained setup STOP. It corrects the Python-Xlib focus-call argument order and exercises the current-main release-batch backend plus its current V4→V3→V12 owner closure. It dispatches key events only to a synthetic, local Xvfb client.

Before running, review `PREREGISTRATION.md` and verify `FREEZE.json` / `SHA256SUMS`. The candidate and auditor run from the repository root:

```sh
wsl -e bash -lc 'python3 -B research/doom/map01_v39_xvfb_per_key_release_identity_a03_20261005/SOURCE/candidate.py --out /mnt/c/Users/junny/Documents/Codex/2026-10-03/new-chat-3/work/agent-interface-v39-perkey-a03/research/doom/map01_v39_xvfb_per_key_release_identity_a03_20261005/results/A03 --display :125'
python research/doom/map01_v39_xvfb_per_key_release_identity_a03_20261005/SOURCE/audit.py --raw research/doom/map01_v39_xvfb_per_key_release_identity_a03_20261005/results/A03/RAW.json --freeze research/doom/map01_v39_xvfb_per_key_release_identity_a03_20261005/FREEZE.json --candidate research/doom/map01_v39_xvfb_per_key_release_identity_a03_20261005/SOURCE/candidate.py --out research/doom/map01_v39_xvfb_per_key_release_identity_a03_20261005/results/A03/AUDIT.json
```

The live private game lane remains unassigned. This synthetic experiment cannot satisfy the V39 threat, recovery, useful-feedback, or MAP01 terminal gates.
