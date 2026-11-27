# Docker/Xvfb caller comparison extension R13

Two additional counterbalanced MAP01 direct-versus-compiled pairs, fresh seeds 2026102917 and 2026102918. One attempt per arm, no retries. All task/effect/release conditions, timer boundary, source mount, and pinned Docker image are identical to R12. The only harness change is a LF-only Bash wrapper that redirects arm stdout/stderr to an evidence log and propagates the real Python exit code without CRLF conversion. Wrapper SHA and all preregistration inputs are frozen before execution.

This extends the small descriptive sample only. It does not establish general speed, reliability, MAP01 completion, model/token savings, Windows, or WSLc behavior.
