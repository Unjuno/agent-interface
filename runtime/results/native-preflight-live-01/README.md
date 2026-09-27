# Native preflight live continuation
Source: 8afc0dcc2214f90c20e58cd4a34736e140f2366c; fresh Calc seed 991292.
The primary viewed the initial image and used an attached second MCP client
to submit an invalid boolean text gap. The error was retained and request-1
was absent at that point. The original managed client then submitted a valid
decision at the same stage/source and retained the same owner PID through finish.
This is two transport connections to one allocation, not same-connection recovery.

Primary image review guided the write/save and format-confirmation actions.
Saved XLSX independently read A1=766, A2=516. Evaluation succeeded; native_status
confirmed owner returncode 0, and the managed SDK client exited 0. Descendant
cleanup is not claimed. Decisions used temporary-file rename publication.
No input replay, helper model or default-policy change. The new input request
uses explicit 10 ms gaps and 250 ms post-action waits. No latency comparison,
human-tempo or token benefit is claimed. The rejected request created no slot,
but that contemporaneous absence check is a tool observation, not reconstructed
from the final archive.
