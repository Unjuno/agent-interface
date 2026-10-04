# A01 invocation record — Issue #7707

The candidate launch request was submitted once from Ubuntu WSL through WSLc 3.0.1.0, with the pinned cached image and isolation settings in `FREEZE.md`. The same live session was observed repeatedly and then terminated with client exit code 1, no stdout/stderr, no candidate file, and an empty output directory. See `STOP.md` for terminal evidence and classification.

Disposition: `STOP_INFRA`; candidate script execution/result unobservable; auditor 0; retries 0. Root cause unknown. No candidate rerun or alternate-runtime substitution was made.
