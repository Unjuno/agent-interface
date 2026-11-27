# A11 combined key and button recovery

A10 passed recovery for two simultaneous keyboard keys. A11 adds one independently controlled left mouse button while retaining a simultaneous allowlisted `a`/`d` key hold. It requires independent X KeyPress/keymap-down for both keys and ButtonPress/pointer-mask-down before session-only SIGKILL; then KeyRelease/keymap-up for both keys and ButtonRelease/pointer-mask-up after; a matching fsynced verified-empty recovery receipt; stopped owner thread; clean service exit; and supervisor-requested clean Xvfb termination.

One candidate invocation; no retries. A11 is a new allocation. It uses an isolated synthetic Xvfb window with explicit focus/surface/geometry identity, no physical device, game or model. The scope is only the actual process-owner input path and does not establish full V15/V39 product control.
