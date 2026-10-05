# Post-hoc diagnosis — not a replacement for formal A01

The immutable formal attempt stopped because strict float equality failed at cohort 15 for `ht_se` by one ULP. Without rerunning either candidate or frozen auditor, a separately labeled read-only diagnostic reconstructed all 20,000 raw candidate records against public and oracle inputs using absolute tolerance `1e-15`.

It found zero fields outside tolerance and computed the preregistered metrics. The HT coverage was `0.94025`, below the frozen `0.944` minimum, so the scientific coverage claim is `FAIL_METHOD` even though the mean and SD gates pass. This post-hoc check establishes neither that the frozen auditor passed nor a new formal allocation. The original `formal_terminal.json` and captured auditor stderr remain the authoritative first-run receipts.
