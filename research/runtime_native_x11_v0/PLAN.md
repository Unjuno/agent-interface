# Native X11 backend v0 — frozen experiment plan

## H

The language-neutral semantic core can admit/refuse programs before a real X11 backend, and admitted keyboard/pointer/focus/capture operations can produce physical/server receipts plus an independently scored application effect without changing common program meaning.

## T

One private Xvfb allocation with four fresh fixture processes:

1. `stale`: stale observation -> `STALE_OBSERVATION`, zero injected events, zero private fixture effects.
2. `expired`: expired lease -> `LEASE_EXPIRED`, zero injected events, zero private fixture effects.
3. `unsupported_text`: current backend declares `input.text=unsupported`; a text program -> `UNSUPPORTED_CAPABILITY`, zero injected events/effects.
4. `valid`: focus fixture; key `A` down; pointer move to window-client point; left button down/up; final `release_all`.

For valid require focus XID agreement, `XQueryKeymap` observes key down, root pointer query matches the requested translated point, XGetImage hash changes after visible input effects, final key/button release verifies empty, and the post-input private fixture ledger contains key press/release and button press/release.

No model, provider, network, shared display, promoted runtime or existing allocation.

## D

PASS only if all refusal arms have zero input/effect, valid arm is admitted and all direct receipts pass, independent scorer passes, and all processes close without held input. `office_ready` must remain false while text/event feedback are unsupported.

## C

X server delivery may not imply application consumption; focus/geometry can race; XGetImage change is not semantic proof; XTest availability can differ by server; keymap state can diverge from application event handling.

## U

Private Xvfb scripted fixture only. No real office application, Wayland, Windows, macOS, Unicode text input, provider tokens or product-performance claim.
