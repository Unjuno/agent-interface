# Active XID and visible-screen divergence — Issue #2907 construction03

Disposition: **PASS_FOCUS_PIXEL_SPLIT_WITH_ACTIVATION_CONTROL** (bounded synthetic X11 mechanism only). Independent raw audit: **PASS_RAW_AUDIT**, 3/3 captures, `errors=[]`. This is not an integrated desktop-task PASS and does not close #2907.

## H/T/D/C/U

- **H:** Direct X input focus can make the requested client the active XID and pass the current-main `NativeHandleBridge.review_window` focus-ancestry gate while a different overlapping client remains visually topmost. EWMH activation should change the topmost stacking entry and visible capture pixels.
- **T:** One fresh local Docker Desktop run, pinned to source commit [`2dadbde`](https://github.com/Unjuno/agent-interface/commit/2dadbde96a3774614f0dff8b51f95dbef9d05716) and image `agent-interface-desktop-integration:local-01` (`sha256:44634c6599b9713b382da9937db38d409c9e66bcbce95aaf2bfeae7793c11385`). Linux/amd64, Xvfb 800x600, Openbox, two fully overlapping colored `xmessage` windows; root/source read-only, `--network none`, no key/pointer content input, model calls, or retries. Exact H/T/D/C/U and frozen operations are in [PLAN.md](PLAN.md).
- **D:** Exact active XIDs, EWMH stacking order, production bridge review receipts, full-screen PNGs and SHA-256, center-pixel values, source closure hashes, process exits and logs are retained here. [audit.py](audit.py) independently decodes the PNG bytes and validates pixel, dimensions, capture hashes, XIDs, stacking and cleanup.
- **C:** PASS only when direct focus yields a reviewed Inkscape surface/active XID while Calc remains topmost and its known red pixel remains in the bridge capture; then EWMH activation must make Inkscape topmost and its known green pixel visible. The frozen result meets this bounded discriminator. No task-completion, general reliability, or product gate is implied.
- **U:** Synthetic windows and a single Xvfb/Openbox stack only. No Calc/Inkscape, public MCP stdio session, user task, or prevalence sample. Whether app-specific activation/focus policy is appropriate remains unresolved. Earlier #2907 real-app mismatch and unmet goals remain authoritative.

## Execution history (all outcomes retained)

1. **Construction01 STOP:** Xvfb/Openbox and both windows started, but the independent Xlib stacking observer lacked `DISPLAY` in its own process environment. It stopped before capture or focus contrast. Raw receipt/logs: [`history/construction01-stop/`](history/construction01-stop/).
2. **Construction02 scoped reproduction:** Correcting that environment setup yielded active Inkscape XID after direct focus, while the bridge screen sample remained Calc red; `review_window` returned `reviewed`. It lacked a positive EWMH-activation control and independent raw auditor. Original receipt, logs and both PNGs: [`history/construction02/`](history/construction02/).
3. **Construction03 frozen follow-up:** Added the positive control and separate byte-level audit. No preceding result was overwritten or relabeled.

## Construction03 observations

The overlapping synthetic windows had XIDs Calc `4194336` (`0x00400020`) and Inkscape `6291488` (`0x00600020`). The baseline active XID was Calc; stacking ended in Calc; the public capture's center pixel was `[216,34,34]`.

After `xdotool windowfocus 6291488`, active XID became Inkscape, but stacking remained `[6291488,4194336]` (Calc topmost). The production bridge returned `reviewed`, `authority_granted=false`, `input_dispatched=false`, with target surface/XID `6291488`; its full-screen capture still contained Calc red `[216,34,34]` at `(400,300)`. This is a direct XID/visible-pixel split, not an inferred app identity based on title.

After `wmctrl -ia 0x00600020`, active XID remained Inkscape, stacking became `[4194336,6291488]` (Inkscape topmost), and a second bridge review returned `reviewed` with the visible center pixel `[34,200,68]`. The raw screenshots are [focus-only](bridge/images/ec9c2180ba224927988d6de3bb00829f.png) and [after EWMH activation](bridge/images/f155aceddc4f40d69e8e7ed5f5e9ad39.png); baseline is [here](bridge/images/bc1fe49f233544dcaed3c3d41563f5f5.png).

| Phase | Active XID | Top of stacking | Bridge surface | Captured center pixel | PNG SHA-256 |
|---|---:|---:|---:|---|---|
| Calc baseline | 4194336 | 4194336 | 4194336 | `[216,34,34]` Calc | `0e65c1df3e8056b9c71a12b7b833c941bfaf7369e8f1f5f43c2bf5e1fc4f6984` |
| Inkscape direct focus only | 6291488 | 4194336 | 6291488 | `[216,34,34]` Calc | `b197cf8dd5ff02ca6704da6208f6284c64f13114c8dd9773d680f0b1d221b74f` |
| Inkscape EWMH activation | 6291488 | 6291488 | 6291488 | `[34,200,68]` Inkscape | `4ac7fd48982899b6896b755f6991988097a93d91bbc808ba420f32f8c287c38b` |

There were three 800x600 physical-screen captures (sequences 1,2,3), binding revisions 0,1,2. All PNG digests matched the native artifact receipts and source raw hashes. The independent audit recomputed the center pixels from the PNG bytes, verified the requested surface IDs and stack order, and returned `PASS_RAW_AUDIT` with zero errors. Both test app processes and Openbox exited 0; Xvfb exited via SIGTERM (`-15`); all four tracked fixture processes reached terminal states. Audit provenance: the first auditor draft trusted the runner's reported center RGB (although it checked PNG digests). That draft was not accepted as an independent pixel audit. Before relying on this result, `audit.py` was corrected to decode and sample the PNG bytes itself, and the immutable `run.json` was audited again in a separate network-disabled container. Only this corrected audit is reported as PASS.

## Reproduction and provenance

`fetch_sources.py` downloads a fixed 19-file current-main source closure into a Docker volume and checks every SHA-256 against the pinned commit. [`source_manifest.json`](source_manifest.json) retains the exact paths, byte counts and hashes. Reproduce in two phases: first create and populate the source volume using network access, then run the experiment and auditor in separate network-disabled containers. Use a **new empty output directory**; do not reuse the retained output directory for another allocation.

```powershell
$study = (Resolve-Path 'research/integration/issue_2907_active_xid_screen_contrast_20260928').Path -replace '\\','/'
$fresh = 'C:/path/to/a-new-empty-output-directory'
docker volume create aiface-src-2dadbde96a3774614f0dff8b51f95dbef9d05716
docker --context desktop-linux run --rm --network bridge --mount "type=volume,source=aiface-src-2dadbde96a3774614f0dff8b51f95dbef9d05716,target=/src" --mount "type=bind,source=$study,target=/study,readonly" --entrypoint python agent-interface-desktop-integration:local-01 /study/fetch_sources.py
docker --context desktop-linux run --rm --network none --read-only --security-opt=no-new-privileges --cap-drop=ALL --cpus=1 --memory=1g --pids-limit=64 --tmpfs /tmp:rw,noexec,nosuid,size=64m --mount "type=volume,source=aiface-src-2dadbde96a3774614f0dff8b51f95dbef9d05716,target=/src,readonly" --mount "type=bind,source=$study,target=/study,readonly" --mount "type=bind,source=$fresh,target=/out" -w /src -e PYTHONPATH=/src/research/live_control:/src --entrypoint python agent-interface-desktop-integration:local-01 /study/run.py
docker --context desktop-linux run --rm --network none --read-only --security-opt=no-new-privileges --cap-drop=ALL --cpus=0.5 --memory=512m --pids-limit=32 --mount "type=bind,source=$fresh,target=/evidence" --entrypoint python agent-interface-desktop-integration:local-01 /evidence/audit.py
```

The expected one-shot runner result is retained in `run.json` (SHA-256 `ec71709bc1f609e1b0733a5b4e0bfaccf60913ad60c84c21d5c3725524f60203`); the independent audit record is `audit.json` (SHA-256 `12b3aea9521e12e348d76d5db2e3bbba1e67092318dac40d8da8f30d1ea51cc7`). Source/image identities and all immutable raw PNGs/logs accompany this report. No runtime/default behavior was changed.

## Integration interpretation

The observation confirms that a positive focus-ancestry/active-XID receipt is not a foreground-pixel proof. In this synthetic Openbox path, EWMH activation raises the window and makes the pixels agree, but #2907's existing fixture already contains `wmctrl -ia`; this experiment does not show that adding activation alone fixes the real-app event. The integration-relevant contract is to keep active-XID/target review and post-action visual evidence distinct, and to score task effects independently. No change to default focus behavior is recommended from this construction alone.

This is independent mechanism evidence complementary to [PR #5000](https://github.com/Unjuno/agent-interface/pull/5000), which adds an optional EWMH activation operation and records a real Calc/Inkscape public-MCP trial. This study does not modify or replace that branch, and it does not validate that PR's implementation; it isolates the focus/stacking/pixel distinction in the current-main production observation bridge.
