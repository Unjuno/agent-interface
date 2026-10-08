# A01 → A02 declared setup delta

A01 is retained unmodified in PR6994, resulthead5a1bfa8ddc6849ae43c5625baa361632b08a5a2e. A02 has newfixture_id/claim; constants add readiness2s andrendezvous1s, watchdog2s→6s. Producer consumes those setup constants and labels watchdog expiry from the actual fixture. Auditor changes only identity/setupconstants; construction adds AST checks of their consumption.

SHA equality with A01 is mandatory for main/send/close/composed/bounded/echo peer source. Scientific request50ms/checkpoint250ms/holderrelease400ms, cellorder, expected outcomes and allfive corruptioncontrols remain unchanged. Setup changes do not regrade any A01 result or prove CPU/mount causal attribution.
