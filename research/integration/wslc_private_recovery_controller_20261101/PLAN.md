# Private display recovery experiment

1. Add tests for identity mismatch, successful fenced retirement, failed retirement, and ordinary cancellation without destructive retirement.
2. Implement a small one-shot experimental coordinator over the exact private-display and guarded-owner objects; never claim the old task or release succeeded.
3. Run focused unit tests and an isolated WSLc trial using real cancellation after owner death, with a fresh-display task and preserved raw evidence.
4. Keep the integration experimental: callers still own the exclusive display and decide how to create the next target; do not expose it via MCP until its lifecycle and failure races are covered.
