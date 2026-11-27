# R27 result — pending dispatch retrieved by exact call ID

The frozen audit passes 14/14. The new supervised Win32 session returned
`pending` after a 10,007.649 ms public dispatch wait. The probe then called
read-only `interface_results` for the exact returned call ID six times; the
first five reported `running`, and the sixth returned `completed` after a total
of 11,059.696 ms from dispatch start. The operation was not cancelled and was
not dispatched again.

The retrieved terminal result carries a verified release receipt at
10,818.808 ms from dispatch start, with empty key/button down and unknown sets,
same-fixture active-desktop witnesses, producer exit code 0, and neutral
independent readback. The fixture journal confirms exactly one click, all 31
expected character events, and one save. The independent effect file matches
the sentinel. The public session closed, the owned fixture exited with code 0,
and the prior foreground window was restored. The close response itself has
`release_confirmed=false`; the terminal dispatch result supplies the separate
verified release receipt. Runtime `task_success` remains null.

This confirms the public pending-result protocol for one supervised Win32
fixture action: keep the server session open and retrieve the exact call ID
before closing. It is one local trial. It does not establish blocked-I/O
release, cancellation recovery in this same session, MAP01, WSLc portability,
matched efficiency, or broad reliability. R24 and R26 remain immutable
`FAIL_OR_UNKNOWN`; their persisted reports showed why exact-call retrieval was
necessary. R25 remains a pre-input `INVALID_RESPONSE_WAIT` stop. The R23
raw/manifest discrepancy remains an explicit limitation.
