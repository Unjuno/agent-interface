# Plan evidence join — 2026-11-04

Question: can a reuse-horizon digest be independently joined from the retained provider response through each public Calc prepare, parent artifact, compiled result, release, and post-close score?

This synthetic check adds a strict four-row evidence join (cold, warm, repair, post-repair warm). It hashes canonical provider plan JSON, binds generation attempts and the public prepare attempt/call, requires the retained plan/digest to match, and requires fresh task, owner, artifact, call, and verifier custody for each task. The effect/release/independent-score fields must all pass. Negative cases cover digest substitution, wrong repair attempt, missing score, cross-task reuse, and stale owner reuse.

Local validation: Windows Python 3.11 and pinned Docker image `agent-interface-xvfb-mcp:late-input-r19` (`sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425`), offline, 2 CPU, 4 GiB memory, 4 GiB memory+swap, 256 PID cap, read-only checkout. Focused evidence-join and existing reuse-horizon validator suites passed 23/23 in normal and optimized mode in both environments. `git diff --check` passed. An initial Docker command used nonexistent `python`; it exited 127 before tests. Retried with the image's `/usr/bin/python3`, both modes passed.

Scope: synthetic validator coverage only; no model generation, provider usage, GUI operation, live Calc effect, WSLc, MAP01, or efficiency result is established. Existing retained runs contain no actual reuse-horizon provider-plan report to validate. This join should be wired to real raw and receipt paths before any such report is counted as live evidence.
