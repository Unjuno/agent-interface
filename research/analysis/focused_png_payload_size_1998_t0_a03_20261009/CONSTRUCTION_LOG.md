# Pre-freeze construction verification

The deterministic fixture builder, candidate serializer, and independent PNG decoder/auditor were built before any formal invocation. Both construction passes ran with `sandbox-exec` denying network access; they do not count as candidate or auditor runs.

- `python3 -B -m unittest discover -s . -p 'test_*.py' -v` — 6 tests passed.
- `python3 -B -O -m unittest discover -s . -p 'test_*.py' -v` — 6 tests passed.
- `git diff --check` — passed before freeze.
- Formal invocation counts at freeze: candidate 0, auditor 0, retries 0.

OrbStack Docker context was `orbstack`. Read-only image inventory stopped before listing images because a containerd content-blob read returned `operation not supported`; no container was started. The formal host fallback is macOS 27.0.1 arm64, CPython 3.14.5 under network-deny sandbox. This is not container evidence.
