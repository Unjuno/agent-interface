# P07 outcome — scoped Fake X pass after additive rescoring

One frozen Codex App Server turn saw the exact public observation image and
selected the green target center `[16, 8]` (10,185 input, 58 output and 39
reasoning tokens). The public mint request used observation sequence 1, and the
owner-side mint receipt records creation on sequence 1. The owner-side Fake X
transport retained exactly one ButtonPress at `[16, 8]`; the synthetic effect
receipt and persisted image independently confirm the success pixel changed to
`[255, 0, 0]`. Both the compiled action receipt and session close confirm all
keys/buttons released.

The original `run/RESULT.json` classified the attempt as a retained first-outcome
failure because the runner searched one directory level too deep for the
owner's click/effect/state files, then reused the initial framebuffer. That raw
record and its SHA-256 manifest remain unchanged. The additive correction audit
recomputes the score from the owner click, effect, persisted pixel, mint,
compiled receipt, release receipt, provider result, and hashes; all 14 checks
pass. Runtime `task_success` remains null.

This is a real-model visual-grounding and standard public-MCP composition pass
on synthetic Fake X only. It does not establish WSLc/live desktop transfer,
MAP01, bounded recovery under blocked I/O, matched efficiency, or reliability.
P07 was run once and not retried.
