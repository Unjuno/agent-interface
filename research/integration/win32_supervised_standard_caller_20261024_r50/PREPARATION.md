# R50 preparation

R50 is a new native-Windows paired replication of the frozen R49 bounded-cancel + fresh-generation task protocol on current main `47d5e9b6c45ecabd682f71731244dbc085ffa88f`. The R49 packet's result, raw, audit and conditions are hash-pinned predecessors. R50 uses unique attempt, program, lease, task token, oracle, call and process/window generation identities. The input-free preflight passed 13/13 before fixture launch.

The phase order was fixed: one phase-1 dispatch and at most one cancel; phase 2 only after the strict 11-check release gate; one dispatch and one server-configured task-oracle call; no retry or replay. Computer Use activated only the exact unique owned fixture windows after screenshot inspection, and the runner independently checked the foreground HWND and owning process. No WSLc or Docker operation was used.

R50 is one attempt. Its phase-2 oracle identifier was generated with UUID hyphens; the public verification API requires 32 lowercase hexadecimal characters. The phase-2 public receipt therefore returned `unknown` even though the fixture wrote the frozen effect. This configuration failure is preserved; it does not establish integrated task success.
