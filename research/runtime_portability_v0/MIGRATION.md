# Migration from Python oracle to product runtime

## Decision

Do not freeze Python classes, import paths, or the current WSL bridge as the
product ABI. Freeze **test vectors + wire semantics + error meanings** first.

A later systems implementation should be considered conformant only if it passes
the same golden vectors produced from this oracle and preserves:

- stale observation/binding refusal;
- bounded authority/lease expiry;
- explicit capability/permission failures;
- coordinate-frame identity;
- held-input accounting and release-all terminal invariant;
- unknown/malformed codec failure;
- persistent dictionary epoch/digest invalidation;
- semantic AST equality across model-boundary codecs.

## Recommended layering

```text
agent/provider adapters
        |
model-visible codec (replaceable)
        |
semantic program + admission core
        |
backend capability trait / vtable
        |
+---------------+---------------+---------------+
| Linux backend | Windows       | macOS         |
| X11/Wayland   | native        | native        |
+---------------+---------------+---------------+
```

The product core should not link to a model SDK. High-frequency control should
stay local; the agent boundary can be IPC/library/tool-call glue outside the motor
loop.

## Systems-language handoff

A memory-safe native implementation (for example Rust) is a plausible product
candidate because it can expose a small C-compatible/local-IPC boundary and bind
native OS APIs. This task does **not** select Rust as a proven winner: the current
container has no Rust toolchain, so no uncompiled systems-language code is added.

The first systems-language task should therefore be mechanical, not semantic:

1. parse the language-neutral fixtures;
2. validate manifests/programs;
3. reproduce the exact admission/error results;
4. reproduce C0/C1/C2 AST equality;
5. only then implement one real backend.

## Backend candidates to validate later

These are implementation candidates, not claims of support:

- Linux/X11: X11 capture + XTEST-style input path, preserving explicit extension
  availability checks and release verification.
- Linux/Wayland: XDG Desktop Portal RemoteDesktop/ScreenCast sessions where the
  compositor grants keyboard/pointer/capture authority.
- Windows: Windows Graphics Capture for frames and SendInput-class input
  injection, with native window/focus/scaling checks around them.
- macOS: ScreenCaptureKit for capture and Core Graphics event synthesis for input,
  with screen-recording/accessibility permissions surfaced explicitly.

Native implementations must not change common program meaning to fit an OS API.
