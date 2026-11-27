# R43 preparation

R43 is a separately frozen, single phase-2 task-effect attempt on native Windows. It repairs only R42's harness scoping defect by passing the already-created Win32 user32 handle into the foreground-marker gate. R42's phase-1 strict release PASS is a predecessor result from a distinct attempt, not a claim of same-attempt pairing.

The new attempt uses one fresh fixture, one public observation, one validation, one dispatch, one independent server-side oracle call, no retry/replay, and a bounded cleanup. The exact CUA window ID/HWND and process owner must match before the marker is accepted. No WSLc or Docker is used.
