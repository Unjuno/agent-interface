# A02 terminal infrastructure stop

The frozen candidate command was invoked once. It exited before candidate cases executed:

```text
ModuleNotFoundError: No module named 'map01_stagnation_v1'
```

Cause: the V39 controller imports sibling research modules by their bare module names. A02 added the repository root to `sys.path` but omitted `research/doom` and `research/live_control`. Candidate cases executed: 0/10. Candidate output file was not created. No scientific PASS/FAIL is assigned. Per the freeze, A02 is not rerun or overwritten. A03 adds both source directories to the bootstrap, uses a new versioned path, and is a new one-shot allocation.
