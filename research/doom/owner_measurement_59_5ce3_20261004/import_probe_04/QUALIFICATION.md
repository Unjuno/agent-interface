# Fixed snapshot qualification, not scientific completion

Source: 96d39ca3855351b2501aab1da919941011190ac3. Image:
sha256:200f0ba1c5b6689261b30f1cc89c26da1b8c8b522fbcbe27b688d55ea67348c5.

First guarded import outcome: PASS_IMPORT_ONLY; 46 repository modules matched
their frozen snapshot bytes; no X11, DoomGame, or subprocess guard attempts.
RESULT.json SHA256: adb65d3b22f2f5dab9b2cc792bbcf2398db3e28e693d1da2d5312846cd24eb34.

Container package CI: 15/15 PASS. Existing fixed-source UTF8 regression: 3/3 PASS.
All three containers exited 0, OOMKilled=false; terminal states and raw CI logs
are retained alongside this note. No model, game, or native control was run.

Tested file SHA256 identities:
- build_owner.py: 1d616039a663d9b4bc242e6d2e314012662b4df12c2a19651b8d619241a8ac00
- test_builder.py: cfacef036a7106a1c156c93f8fd372aa00bedcfd39d153e73e0bbb4191e547dc
- test_import_probe.py: ed2b03e2158c26bf11371c25800511447b2c9bfb8b45f5cf1366e352515c62d1
- probe_imports.py: 401b5b612e4b3af6900574a2fc6baa2c406c6ab98aab7280564c542969ec235a

Package test command: image entrypoint Python, `-m unittest discover -s
/work/research/doom/owner_measurement_59_5ce3_20261004 -v`, environment
OWNER_MEASUREMENT_SOURCE_ROOT=/source. UTF8 command: `-m unittest
test_app_server_utf8 -v`, cwd /source/research/live_control. Source read-only;
network none; requested 1 CPU, 512 MiB memory/swap, 128 PIDs, read-only root,
64 MiB /tmp tmpfs. These settings are not measured resource enforcement.

Earlier STOP and PASS artifacts are unchanged. This supersedes neither earlier
outcomes nor missing live authority. Per-key native timing, independent TASK_EFFECT,
matched recovery, telemetry perturbation, and fresh independent review remain
unverified. No merge-ready or current-main-wide CI claim follows from this scope.
