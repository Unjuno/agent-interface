# A34 preregistration

Distinct one-shot allocation `MAP01-V39-WSLC-XVFB-APP-EFFECT-A34-20261014-01`; prior A30-A33 outcomes remain preserved and are not retried. Fixed 300ms lease begins before V4 down call. Check dispatch context (owner/operation/key/intent/deadline) separately from actual V4 admission receipt (event/key/keycode/intent/ack/deadline); require matching app KeyPress and counter 0→1 within 200ms, expiry KeyRelease and server keymap up within 1s, owner expiry receipt accepted by exact current-main terminal predicate, owner close/thread stopped, Xvfb exit 0, frozen hashes intact. Independent audit decides PASS; post-dispatch failures FAIL.

Cached WSLc image exact ID in freeze, pull never, network none, 1 CPU/1GiB requested. Unix X11 socket :143, TCP off; run as image default root; read-only source/runtime and new writable output path. Bash runner is LF-only and SHA-bound. No game/model/Windows GUI/physical input. No retries.
