# Docker/Xvfb caller comparison extension R14

Two additional counterbalanced direct-versus-compiled pairs using fresh seeds 2026102919 and 2026102920. One attempt per arm, no retries. Same pinned image and R10 task/effect/release conditions, timer boundary, read-only source/root, network disabled, Xvfb and evidence layout. Wrapper uses LF-only script and writes stdout under `/tmp` first so the Python harness creates its own previously nonexistent arm output folder; after completion the raw stdout is copied beside `result.json`. The real Python exit status is propagated. Source and preregistration are frozen before launch.

This remains descriptive local Docker/Xvfb evidence only. It does not claim general speed, reliability, MAP01 completion, model savings, Windows or WSLc behavior.
