# Issue #59 — POSIX SIGINT publication-order construction probe

A synthetic, isolated confirmation of the pending-SIGINT/final-publication ordering reviewed in F03 `cd51958`. It writes a PASS file while SIGINT is blocked, queues SIGINT, restores the mask, and observes the child process and saved file from its parent.

The preliminary inline attempt was inadequate: its displayed `130` was a simulated value, not the child process status. It is retained as a superseded output. The corrected saved probe observes the real subprocess result.

The probe does not import or execute F03, and is not an F03 construction gate, formal allocation, custody audit, or computer-control result. The audit checks the saved output, complete package hashes, text control bytes, and optionally committed Git blobs. It is authored by the same worker and is not an independent review. See [METHOD.md](METHOD.md), [RESULT.md](RESULT.md), retained stdout, and the saved-output auditor.
