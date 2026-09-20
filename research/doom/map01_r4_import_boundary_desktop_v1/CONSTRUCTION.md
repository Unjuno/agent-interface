# Construction log

- First unit-test attempt: discovery initially failed because `tests/` did not include the additive parent on `sys.path`; test discovery was corrected.
- Second attempt: 2 assertions failed. The candidate walked into lambda bodies and labeled every `try` suite conditional; the `try/finally` target call is module-executed. Both classifier implementations were adjusted independently: lambda bodies are deferred, and module-level `try`/`finally` suites are traversed as module execution while exception handlers remain conditional.
- Two formal launcher preflights stopped before Docker: first the repo-root path was too shallow; after changing it, it remained too deep. No container was invoked and no output directory was created. The path was recalculated from `research/doom/<experiment>` to the repository root and corrected; the final script SHA is recorded in the manifest and Issue #3903.
- These were preformal construction checks. No frozen formal invocation, historical import/compile/execute, game, model, or input occurred. The first formal Docker invocation remains unused.
