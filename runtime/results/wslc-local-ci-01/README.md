# WSL containers local CI route

WSL 3.0.1.0 already includes C:/Program Files/WSL/wslc.exe; it was not on PATH.
Direct invocation worked without modifying system PATH or restarting Ubuntu,
Docker Desktop or other WSL workloads. No live/model/GUI benchmark was allocated.

First explicit private-session enter failed with ERROR_PATH_NOT_FOUND and ended.
The failure is retained, not presented as successful dedicated-session isolation.
Session inventory was empty before the following default-session image pull.
Only one test container ran, in foreground, --rm, with network none and a readonly
Windows source mount. python:3.12-slim resolved to Python 3.12.14, OCI repo digest
sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f.

Source file was exported byte-for-byte from parent PR #6077 head
0c20566f59a2bc65b8a945c162d57febef053189. The same unittest command as its replay
workflow ran with WSLc replacing Docker and passed both deterministic tests.
This is local command/image-family coverage, not the GitHub runner or remote
replay-gate completion. The workflow uses a mutable tag; do not infer that a later
GitHub execution necessarily resolves to the same digest. Exact source hash is
in source.json. Real DOOM play and input timing are outside this check.

Original primary tool requests/outputs for failed session setup, image pull and
successful container replay are extracted from this caller's own log only, with
source line digests in source-record-index.json. No other chat was read. Each
tool may also contain a small related inventory/cleanup read, visible in source.
This is retained execution evidence, not a second run of the deterministic suite.

WSLc is not a drop-in substitute for all Docker CI commands: its installed run
help lacks several options used by the golden pinned-container audit (readonly
root, pids limit, cap-drop and security-opt). Do not silently weaken those controls
or claim full Docker parity. That remote golden audit already passed; it was not
rerun unnecessarily. WSLc is now usable for compatible local container checks;
Docker Desktop's earlier unresponsive engine is not claimed repaired.
