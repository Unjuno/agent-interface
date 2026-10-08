# Issue #4124 remote-branch recovery status

This is an exact preservation of the pre-formal source freeze, not a formal
result or authorization to execute its allocation.

- Original branch head: `ac678beaf0fee0dc03716d1b5b250b5fafd6e823`.
- Original seven-file additive tree is preserved unchanged.
- The 6,708-byte source archive was read back and matched SHA-256
  `384ea109a4553160fff66ecfe1a7d439072d27b315b96bc9cae978c6a9caf2ea`.
  Its 12 flat regular members were path-checked; all 11 source files in
  `FREEZE.json` matched their frozen SHA-256 values, and the embedded freeze
  matched the committed freeze.
- The frozen allocation remains 0/16 formal cases (0/2 batches). The branch's
  `CONSTRUCTION.md` records six excluded cases, 45 checks, errors=[]; this
  recovery only verified the archived bytes and did not rerun those cases.
- The formal target is Linux x86_64 / CPython 3.13.5. The local recovery host
  was macOS arm64 / CPython 3.14.5; it performed archive/hash readback only.
  No Docker/container, formal batch, model, network, GUI, or user-desktop
  action was started. Coordination Issue #5085 has no assignment for #4124.
- PR #5072 and its managed-MCP/Calc construction evidence are a later,
  distinct integration check. They do not consume, substitute for, or close
  this frozen 16-case allocation.

The experiment remains prospectively frozen and unconsumed. Issue #4124 stays
open; a future owner must obtain the exact exclusive lane required by #5085
before starting any container work. This record makes the immutable source
available on `main` and does not claim that the experiment passed.
