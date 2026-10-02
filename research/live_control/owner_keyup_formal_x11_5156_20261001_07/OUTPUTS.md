# Allocation 07 output policy

The `results/formal-01/` bind-mount starts with only the tracked `.gitkeep`
marker. At start, require that exact directory contents and no `raw.jsonl` or
`audit.json`. Preserve any candidate/auditor output immutably after invocation;
never overwrite a consumed run. The marker is not experimental evidence.
