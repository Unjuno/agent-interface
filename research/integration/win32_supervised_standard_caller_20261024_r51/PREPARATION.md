# R51 preparation

R51 is a new paired native-Windows attempt on current main `47d5e9b6c45ecabd682f71731244dbc085ffa88f`. It follows the same frozen bounded-cancel and distinct-generation task protocol as R49/R50. R50 is preserved as the immediate predecessor and remains `FAIL_OR_UNKNOWN` because its generated oracle ID contained hyphens. R51 changes the new IDs and adds an input-free preflight requiring the task oracle ID to match exactly 32 lowercase hexadecimal characters. The regression preflight rejects a dashed UUID and accepts `uuid4().hex`.

R51's input-free preflight passed 14/14 before launch, including source/condition/predecessor hashes, native Windows, same-domain QPC timing, and the new oracle-ID format check. The attempt allowed one phase-1 dispatch and at most one cancel; phase 2 began only after strict phase-1 release PASS; phase 2 used a fresh fixture/process/window/generation and one public task verification. No retry/replay was allowed.

Only unique owned fixture windows were activated through Computer Use after screenshot inspection. The runner separately confirmed foreground HWND and process ownership. WSLc and Docker were not used.
