# Runtime portability v0

This directory is an **integration experiment**, not a promoted runtime.

It addresses four boundaries that must be separated before Agent Interface can
become a credible cross-platform product:

1. **Semantic core** — model/provider/OS-neutral program meaning and fail-closed
   admission rules.
2. **Backend contract** — explicit capabilities, permissions, coordinate frames,
   freshness, leases and release semantics.
3. **Model-boundary codec** — replaceable serialization that always resolves to
   the same validated semantic AST.
4. **Implementation language** — Python remains an executable research oracle;
   the final runtime can be reimplemented without inheriting Python object/API
   layout as its ABI.

The universal office-control floor in this v0 contract is screenshot capture,
keyboard, text, pointer, scroll, focus, release-all, display geometry, monotonic
clock and event/feedback. Clipboard, window enumeration and accessibility are
optional optimizers rather than correctness prerequisites.

## Platform direction (not support claims)

- Linux/X11: current repository evidence supplies the scoped reference path.
- Linux/Wayland: treat as a separate backend with explicit permission/session
  acquisition; never infer support from X11/WSLg.
- Windows: native backend must supply capture/input/focus/geometry/release through
  the same contract; WSLg is not native Windows support.
- macOS: native backend must expose the same semantics and surface permissions as
  typed capability/permission outcomes.

The contract intentionally permits `supported`, `unsupported`, `unknown`, and
`permission_required`; an implementation cannot turn missing capability evidence
into success by omission.

## Codec rule

`codec.py` keeps C0/C1/C2 outside the semantic core. C1/C2 are allowed to be
shorter only because decoding reconstructs the same object accepted by
`contract.validate_program`. A stale persistent dictionary epoch/digest is an
error, never a guess.

UTF-8 bytes and characters are serialization proxies. Exact provider token
claims require the exact tested tokenizer/API usage record.
