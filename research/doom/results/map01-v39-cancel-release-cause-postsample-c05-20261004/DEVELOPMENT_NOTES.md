# Development and execution notes

- Kept the parent PR branch untouched; the regression test and this evidence package are additive and based on its exact head.
- A first import attempt without putting `research/live_control` on `sys.path` discovered zero runnable tests (`ModuleNotFoundError`); the standalone test now inserts its own directory explicitly.
- An exploratory extension that reused the existing fixture in a second test hit the fixture's cached-display assumption (`IndexError`); the final standalone test uses a fresh fixture setup and passes.
- The parent control failed at `StopIteration` because there was no `input_released` event. The candidate passed with the cancel-specific receipt preceding terminal publication.
- Container execution was not possible without fetching/building an image. To avoid changing a shared OrbStack allocation or obscuring provenance, execution stayed on the host and is explicitly not reported as container validation.
- These failures and environment limits are retained here rather than omitted from the result.
