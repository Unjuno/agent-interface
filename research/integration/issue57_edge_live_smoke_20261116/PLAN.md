# Edge local task-effect smoke (2026-11-16)

## Purpose and scope

Run the existing Windows Edge/OCR/compiled-GUI integration smoke as a
screening check for a live task effect. It uses a temporary Edge profile, a
loopback-only synthetic form, Windows OCR, the current compiled form caller,
and an independent local HTTP server oracle. The model contract is an offline
test double; this run is not a provider or token-efficiency comparison and is
not a formal Issue #57 allocation.

## Frozen condition

- One task; at most two harness invocations, and no retry after any input
  dispatch. Invocation 1 failed during OCR worker startup before any input
  dispatch because this sparse checkout omitted the worker script. Invocation
  2 is a fresh process/profile after adding that exact source file from main.
- Synthetic field value: `t991025-1`.
- The integrated caller may submit only after OCR confirms the exact value.
- The independent server must receive exactly one POST containing exactly
  `value=t991025-1` and return the success page.
- The compiled receipt must report one completed transition, verified release,
  and zero frontier-model resumptions.
- Any missing OCR, uncertain submission, duplicate/wrong POST, or cleanup
  failure is a failed/unknown smoke; do not retry this allocation.

## Preservation

Invocation 1's observed failure is retained in `attempt-01.log`; invocation 2
will be captured in `attempt-02.log`. The authoritative implementation and
assertions are pinned by the source commit and file hash in `RUN.json`. The
existing test uses a fresh temporary profile and attempts to delete its
screenshots/server state at teardown. Invocation 2's cleanup failed, leaving
the exact temporary profile noted in `RUN.json`; this archive retains process
transcripts and code identity, not pixel captures or per-request JSON.
