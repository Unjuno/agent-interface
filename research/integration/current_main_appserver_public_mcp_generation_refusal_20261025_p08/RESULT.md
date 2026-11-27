# P08 outcome — stale process generation refused before input

One preregistered App Server turn selected the green target point `[16, 8]`
from the exact public observation image (10,185 input, 60 output and 41
reasoning tokens). After the response completed and before public mint, the
runner signaled the child-owned Fake X identity reader to change the target
process generation from `a*64` to `b*64`. The old observation and minted alias
remained tied to sequence 1 / generation `a*64`.

The standard public compiled caller then returned `SAFE_YIELD` with reason
`association_changed`: zero completed transitions and one admission refusal.
The owner input log is empty, there is no click/effect receipt, the application
image is unchanged, and close verified neutral release. The all-attempt ledger
is complete; the independent refusal oracle passed. Runtime `task_success`
remains null. Local tests passed 4/4 and the frozen audit passed 14/14, including
the prelaunch source hashes and raw manifest.

This is one real-model stale-generation refusal on synthetic Fake X. It does
not establish physical release under blocked I/O, WSLc/live GUI transfer,
MAP01, matched efficiency or reliability. P08 was run once and not retried.
