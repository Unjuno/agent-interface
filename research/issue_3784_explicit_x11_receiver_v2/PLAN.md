# Issue #3791 — corrected receiver-control allocation

## H / T / D / C / U

**H** — #3784 formal-01 reached a mapped/focused InputOnly receiver and observed its XTEST control, but the preregistered control oracle was wrong: XLookupString returned `a` on both KeyPress and KeyRelease. This new allocation accepts the observed behavior and will proceed to the frozen backend, which is hypothesized to deliver `=B2*A2` under the verified standard German map.

**T** — One formal allocation, `issue3784-explicit-x11-receiver-formal-02`, with three fresh German Xvfb `-noreset` rows and one US control. Each row maps/focuses an InputOnly receiver selecting press/release and requires a control key whose two event types, keycode, keysym and XLookupString text exactly match pinned-image construction evidence. Capture US baseline query/server dump/fresh Xlib core map; on DE rows apply exactly `setxkbmap -layout de`; verify active query/dump/fresh map. Reject `=B2*A2€` before zero events/emissions, then call current-main `_text_plan` and emit `=B2*A2` once. Preserve all events, plan, counts, releases, source/artifact hashes and process cleanup. Audit the result independently in a second no-network container. No retries.

**D** — PASS only if all four receiver controls/focus gates pass; all three German maps and US control are confirmed; unsupported payload is refused with zero emissions/events; every row receives exact formula and planned full press/release trace; physical key/button release is verified empty; and independent audit verifies all hashes/artifacts. Setup gate uncertainty is STOP/HOLD. Incorrect formula, unexpected/missing events, unsupported emission or failed release is FAIL. A setup STOP gives no candidate result.

**C** — OrbStack Docker, Linux/arm64, pinned image `agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27`; network none; read-only source/root and isolated output; no host display/input, GUI app, install or model. Candidate blob `9cae101a219348077668c8fc086acf8e13154afe` on frozen base `f5f9ff842fd061e6e1eb2f43a17cc7785b807fc7`.

**U** — Exact backend, pinned Xvfb and standard German two-level XKB only. No Calc/task effect, physical keyboard, IME/Compose/dead-key/level-3, other layouts/backends, performance or product claim. The combined receiver plus `-noreset` configuration does not isolate which prevents a server reset.

## Construction vs formal

The construction test asserts focus identity plus exact XTEST control events and XLookupString results for both event types. It is not part of the four formal rows. Freeze the current-main source manifest, runner/auditor hashes and result gates before the formal container run.

