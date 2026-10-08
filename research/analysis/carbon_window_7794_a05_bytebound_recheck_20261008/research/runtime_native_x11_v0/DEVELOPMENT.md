# Development calibration before freeze

- Environment preflight found X11 headers/lib and runtime `libXtst.so.6`, but no XTest development header/pkg-config metadata. The candidate therefore uses `dlopen`/`dlsym` and treats XTest absence as an explicit capability failure.
- First backend build failed from a `typedef` typo in manually declared XTest function pointers and from trying to call the C `DefaultScreen` macro directly through cgo. A C wrapper repaired the macro boundary.
- The first private-Xvfb calibration then passed: valid input produced focus/key/pointer/capture/release receipts and four independent fixture events; stale and expired controls injected zero input/effects.
- Before freeze, an explicit `unsupported_text` refusal arm was added because this v0 backend does not yet implement generic text injection or event-feedback semantics. This prevents a partial X11 mechanism from being mislabeled office-ready.
