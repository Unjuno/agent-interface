# First launch stop

The first runner attempt ended before constructing the native backend or sending any input:

```text
ModuleNotFoundError: No module named 'runtime'
```

Cause: direct script execution placed the experiment directory on `sys.path` but not the repository root. The runner was changed to add its resolved repository root before importing `runtime`. No `result.json` existed and candidate input executions were zero at that stop. The single candidate probe ran after this repair and is retained in `result.json`.
