# R13 outcome: recovered release and bounded close passed

The frozen public stdio-MCP trial passed **19/19** checks at source commit
`3af0a4563c50f64e93e77e3fbed5c63996c1fe3d` with a clean tracked tree. Same-call
status polling reached the hook barrier in 775.292 ms. The owned hook held the
injected Q-down through the single public cancel response (1.495 ms); the exact
producer exited, the public result reached `recovered` with
`release_confirmed=true`, and a separate same-generation process observed Q-up
within 235.151 ms of cancel start.

The R13 fixture saved the exact sentinel
`SUPERVISED-MCP-OK-20261024-R13`. Public `interface_close` returned `closed` on
its first attempt in 90.154 ms. The fixture exited with code 0, the hook thread
exited, and the previous foreground window was restored. Runtime
`task_success` remained null; the independent saved effect is not represented as
a runtime task-success claim.

This is one local Windows fixture result. It does not establish MAP01, broad
reliability, matched efficiency, hard real-time bounds, or transfer to WSLc,
Linux, or other applications. R09, R10, R11, and R12 remain preserved with their
original outcomes. Raw responses, conditions, preflight, audit, process/event
artifacts, and hashes are retained in this packet. No input was sent during the
preflight; R13 itself was executed once and must not be replayed.
