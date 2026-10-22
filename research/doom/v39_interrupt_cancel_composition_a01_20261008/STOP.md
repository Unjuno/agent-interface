# A01 terminal infrastructure stop

The frozen candidate command was invoked once. It exited before candidate logic or case execution:

```text
ModuleNotFoundError: No module named 'research'
```

Cause: when Python executes a file by path, the script directory—not the repository root—was placed on `sys.path`; the frozen command omitted an explicit root bootstrap. Candidate cases executed: 0/10. Candidate output file was not created. No scientific PASS/FAIL is assigned. Per the freeze, A01 is not rerun or overwritten. Successor A02 fixes only the runner's repository-root import bootstrap and receives a new one-shot allocation.
