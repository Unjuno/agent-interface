# Native X11 sub-ms text robustness v1

Repeated-session calibration of the compiled Go+cgo/XTest strict-lowercase-ASCII text path from PR #145.

A deterministic builder applies one research-only pacing change to the frozen dependency: the post-character `time.Sleep` is replaced by a bounded monotonic busy-wait so requested sub-ms delays are actually observable. This is a measurement mechanism, not a production CPU-efficiency recommendation and not a generic Unicode/IME text implementation.
