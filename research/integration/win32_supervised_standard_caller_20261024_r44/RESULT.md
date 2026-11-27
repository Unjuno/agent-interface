# R44 result — 2026-10-24

Status: PASS_SCOPED. The same frozen attempt passed the strict phase-1 release gate (11/11) and the paired fresh-generation task audit (12/12). Both phase exit codes were 0. Raw, conditions, receipts, screenshots, event logs, oracle evidence and audits are sealed in `SHA256SUMS`.

The input-free preflight passed all 12 checks against main `e6192a4294aac0d94d51e75b24583216c718d654`. In each phase, CUA returned one exact fixture window; the screenshot was inspected; the CUA window ID, fixture HWND, independent foreground HWND and owning process matched before the public interface calls.

Phase 1 made one dispatch and one cancel. The call remained `running` before cancellation. The Q-up callback stayed held for 1,260.371 ms after the cancel response (frozen minimum: 1,250 ms), while the caller completed 80 same-call status polls (minimum: 21). An independent same-generation state sampler observed Q-up after the injected key-up return, with 60 eligible samples before callback return. The producer, hook, session and fixture retired cleanly; fixture exit code was 0 and the prior foreground was restored.

Only after that strict gate passed, phase 2 used a new fixture process, target generation, MCP session, call and operation. The exact click/save/text effect matched the frozen expectation. The independent server oracle verified the task and bound its receipt to the phase-2 call, operation, target generation and oracle ID. The terminal release receipt had no keys/buttons down or unknown and contained independent state-query witnesses. Runtime-level `task_success` remains null; the independently verified server-oracle result is `task_success=true`.

This one paired native-PC sample advances the bounded-release and fresh-generation task-effect chain on the local Windows fixture. It does not establish WSLc eligibility or behavior, MAP01, broad reliability, matched efficiency, or real-application transfer.
