# Excluded harness attempts

These attempts did not produce product evidence and are not included in the
passing test counts.

1. The first three-test invocation ran from the research subdirectory without
   the repository root on `PYTHONPATH`; all three unittest selectors failed
   import with `ModuleNotFoundError: No module named 'runtime'`. Re-running
   with `PYTHONPATH` set to the repository root resolved discovery.
2. The first changed-generation negative case altered only the score receipt,
   leaving its public MCP observation body unchanged. The validator correctly
   stopped at the receipt/body mismatch before reaching the intended
   dispatch-generation check. The test was corrected to change the measurement
   and public body together; the corrected negative case now reaches and passes
   the exact action-generation rejection check.
