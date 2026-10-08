# Issue #3794 — focused receiver KeyRelease oracle and German XKB delivery

## H / T / D / C / U

**H** — When character content is counted only on KeyPress and KeyRelease is checked as a matching release (not as an empty XLookupString), the current-main X11 backend will deliver `=B2*A2` to a focused InputOnly receiver on standard German XKB and US control. Unsupported trailing `€` will be refused before any receiver event or backend emission.

**T** — One fresh allocation `issue-3794-german-xkb-receiver-release-audit-formal-01`; source base `1355ff9c0e89e04887e7dd3a08aaa93c7b650df0`, candidate blob `9cae101a219348077668c8fc086acf8e13154afe`. Three fresh Xvfb German rows and one US control, all `-noreset`. Verify baseline US query, server dump, and fresh-client core map; apply exactly one `setxkbmap -layout de` on each German row and capture query/dump/map. Create/map/focus an InputOnly KeyPress|KeyRelease receiver, verify `GetInputFocus`, then receiver-only XTEST `a` control: exactly one press decoding to `a` and a matching keycode release; release lookup bytes are recorded but not treated as a character. Run public `preflight` on unsupported and valid text with zero emissions/events, then plan and emit `=B2*A2` exactly once. Preserve every raw trace, map, stderr, process lifecycle and hash; run the independent auditor in a second no-network container. No retry.

**D** — PASS only if all four receiver/control rows pass, all maps match their requested layouts and DE maps differ from US, unsupported preflight refuses with zero emissions/events, valid preflight is zero-emission, candidate KeyPress text is exactly the formula, event press/release trace matches the frozen plan, all keys/buttons are released, and independent audit confirms source and artifact integrity and rejects corruption challenges. Wrong/missing/extra candidate events/text or failed refusal/release is FAIL. Setup, harness, or integrity problem is STOP, never a candidate verdict.

**C** — OrbStack Docker Engine 29.4.0, linux/arm64, immutable image `agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27`, no network, read-only source/root, private Xvfb only, distinct writable formal and audit outputs. No host display, physical input, GUI app, model, or app data.

**U** — This X11 backend, private Xvfb/XTEST and standard German two-level XKB only. No Calc/task effect, physical keyboard, IME/Compose/dead-key/level-3, other backend/layout, performance, or product claim.

## Freeze record

- Runner, auditor, this plan, source manifest, image digest and invocation are frozen in the preregistration commit before formal execution.
- Frozen source base: `1355ff9c0e89e04887e7dd3a08aaa93c7b650df0`; candidate backend blob: `9cae101a219348077668c8fc086acf8e13154afe`.
- Frozen runner SHA-256: `604ff7238e7ba6053456787520696589bbd7cd9d6ffc877fe771b2ab82d7eb50`; manifest SHA-256: `34be24b090cbcaec586613a868ecd7a16008d8977b4f7073c9dee70d593e8a6d`.
- Auditor SHA-256: `99ea3659b837f6c81db653a945fdd8a4cf360e67acb74626ee459bd765141c02`; it binds both values above.
- Formal and audit output directories must be empty before use; each allocation runs once and is never reused.
- Construction checks are setup evidence only, not formal rows.
- Formal logs are stored separately from container stdout/stderr.
