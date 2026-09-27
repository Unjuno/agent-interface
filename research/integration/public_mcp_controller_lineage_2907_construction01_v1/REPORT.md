# Issue #2907 — caller-owned runtime session lineage construction

## Result

construction04 completed in local Docker. Three explicit app-owned X11 windows (Inkscape, LibreOffice Calc, Chromium) were observed through one X11RuntimeSession and one backend object. Each observation returned an image artifact, input_dispatched=false, side_effect_authority=false. A stale observation-sequence dispatch was refused specifically as STALE_OBSERVATION with backend_emissions=0. A fresh sequence dispatched ESC followed by release_all and completed; the dispatch release and independent final backend release both verified empty keys/buttons. authority_granted=false. This is a scoped construction PASS if and only if the separate audit04 returns PASS_RAW_AUDIT with errors=[].

Runner: construction_v3.py, SHA-256 CDF7A51EADEBBE9114E6C5DBF90CE882A1463E163FBD1693F7E0620101A5230C. Image: public-mcp-three-app-2907:formal01, sha256:b2b42660e35475baf5ef7a546a8c6901c39f04f69266cd9eebfe49c7ed49ea09, linux/amd64. Base image ID sha256:eaf46582f96fd46a1ad6a240928b4c2a828de3d058a4b1490bbadf708d5a52d3. Docker used --pull=never, --network none, pids 512, memory 4g, CPUs 4; source was read-only. No GitHub workflow or model was invoked.

Raw lineage SHA-256: 5699c022ddfac9877ea6f06da270ed07f168e9b2f86942e65930ca1b48ebbb39. The result and three PNG artifacts are retained under evidence/construction04/.

## Audit and historical outcomes

The raw-only independent audit is a separate network-disabled/read-only Docker invocation and checks schema/order, distinct target IDs, artifact SHA-256, the exact stale refusal with zero emissions, successful neutral dispatch/release, authority=false, and five Git blob IDs against main. construction01 and construction03 are not pooled: #01 stopped in app identification; #03 used an invalid expiry and did not reach the stale-sequence gate. See FREEZE.md for all preflight and setup outcomes.

## Boundary

This tests a caller-owned runtime session, not the session privately owned inside the public MCP server. It does not execute the full frozen four-transition mixed-app schedule, exercise typed controller binding refresh for focus/modal/window replacement, or independently score app-specific effects. It is not the #2907 integrated-controller PASS, #2789 six-task convergence PASS, a runtime promotion, model/task success, or a roadmap-completion claim. No runtime implementation was changed.

