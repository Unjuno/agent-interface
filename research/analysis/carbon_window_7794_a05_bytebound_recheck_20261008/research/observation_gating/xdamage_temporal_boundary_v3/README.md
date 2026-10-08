# XDamage temporal-boundary v3 successor

Successor experiment for #4893, kept additive to the earlier v2 stop record.

- Allocation: `xdamage-temporal-boundary-3935-v3-20260927-01`
- Frozen base: `c1e6f24d259f96b4d4dbf211e83fcdf6b9e0a4dd`
- Docker image: `agent-interface-gtk-preflight:local` (`sha256:e2a7634d2b9627ec037c488d6aa472c6c00d5ef0dda6e302f7dced8b9b8752d4`)
- Local-only execution: `powershell -ExecutionPolicy Bypass -File .\run_container.ps1 -Mode construction`; formal mode is permitted only after construction and its independent audit pass.
- Network disabled in container; no GitHub Actions/workflow execution.
- Construction and formal output folders must be new and are separate. Formal mode is a one-shot allocation.
- The runner/auditor and source are frozen and independently read back from Git before any Xvfb or experimental case starts.
- Scope: XDamage event observation around temporal boundaries. No action authority, no GUI-control claim.
