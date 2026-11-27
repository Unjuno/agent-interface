# Live XRes bystander-reuse refusal — R01

**Status before execution:** pre-measurement freeze; one case, no retry. The target is one private Xvfb `:177` instance in local Ubuntu WSL2, not WSLc or Docker.

The experiment checks whether the current-main cleanup worker refuses to send XTest release when a different client naturally reuses the retired owner's XRes resource base. A disposable owner emits one isolated synthetic key-down; after it exits, the first bystander connection must naturally reuse the exact base while independent keymap readback still sees the key down. The cleanup worker is prestarted before the owner and runs the unchanged `x11_cancel_worker` source from the frozen main. No XID forcing, repeated connection attempts, retries, replacement trials, or environment installs are allowed.

The frozen procedure, exact source blobs, environment and stop rule are in [`raw/r01/CONDITIONS.json`](raw/r01/CONDITIONS.json). The one-shot live output, process exit codes, Xvfb log, independent-state snapshots and hashes will be retained under `raw/r01/`. If natural base reuse or the held state is not exposed, preserve HOLD; do not rerun.

This test is a live X server worker-path discriminator, not a public-MCP composition or release guarantee. It does not establish exclusive ownership of global input, hard OS bounds, physical desktop/MAP01 behavior, task success, efficiency, reliability or WSLc portability.
