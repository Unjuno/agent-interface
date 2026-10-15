# V39 Executor pipe recovery composition

**Goal:** Move current cancellation/recovery qualification across actual owned child-process stdin/stdout and real Executor v12/v13 workers, keeping native/game/model absent.

**Base:** `3e02dec0bf49676ab0ba330b2a3cb97f2925dac4`.

**Architecture:** Test-only child protocol shim dispatches to actual Executor.submit/cancel/close with a synthetic backend. Backend releases its simulated held key, emits recovered observations and deliberately withholds terminal finalization. Parent uses current controller cancel helper and exact wait AST on a real stdout reader queue. Verify cancel/owner-release is not terminal, planner interruption waits for closure, original invalidation remains denied and fresh full frame retained. Check unknown cleanup and explicit dropped-invalidation countercontrol on both default v12 and measurement v13. Test shim is not real session main.

**Constraints:** Only owned Python processes, pipes, in-memory backend/keys/signals. No X/native/game/provider/WSL/container/allocation or old producer. Synthetic release is not physical release or OS timing guarantee. Cleanup must join reader/worker processes, retaining forced cleanup as failure.

- [x] Add tests/child shim with raw pipe rows and terminal barrier for both Executor selections.
- [x] Run affected local tests normal/-O, retain exact source/conditions/processes and independent saved readback; preserve all failures.
- [ ] Publish scope and remaining actual-session/backend boundaries, review immutable patch and integrate.
