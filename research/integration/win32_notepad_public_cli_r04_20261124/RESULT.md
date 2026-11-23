# Win32 public runtime CLI Notepad task R04

**Scoped pass: one fresh public CLI task with Computer Control foreground
activation.** The deterministic runtime zipapp is 790,952 bytes, SHA-256
`56ced08ca480dd2217d606328fefda5d30d0ff0d304b6db4c4bfa2431a4e596b`. All 65
packaged source files match baseline main
`22aba58c276141401a7688be335be5191ec661b9`; the manifest audit passed and
doctor selected `win32-v1` without side-effect authority.

The unique Notepad HWND 204624 / PID 4428 was selected from Computer Control's
returned app/window inventory, activated, and independently read back as the
foreground target before dispatch. A fresh public CLI observation returned a
matching target generation. The one dispatch completed normally, with 58
program emissions (60 total including release events) and no recovery or
cleanup error. Terminal release is verified: Ctrl and S key-up calls returned
success, keys/buttons down and unknown are empty, and release errors are empty.

The post-dispatch public observation succeeded with the same target generation
and native HWND. The independent file oracle found exactly the 27 UTF-8 bytes
`AI-WIN32-NOTEPAD-R04-9C27E1` and no extra bytes; its SHA-256 is
`e0e364fab5c45b55ea5e5c316bbf4c5ca8424fd37fa121b9115eb8792a74f025`. The
retained post image displays the same token. The target was closed with normal
`WM_CLOSE` after preserving the outcome.

This passes only a single local public CLI task and ordinary release on this
Notepad/host setup. It does not establish repeated reliability, expiry or
delayed-operation recovery, standard MCP/provider accounting, matched
efficiency, MAP01, or research-preview graduation. R01 remains a packaging
setup stop; R02 remains a frozen target-name setup stop; R03 remains a
foreground-admission stop without input. Their records are not pooled into this
pass.

See [CONDITIONS.md](CONDITIONS.md) and the raw activation, observation,
dispatch, release, file-oracle, identity, and cleanup receipts under `run/` and
`target/`.
