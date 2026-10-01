# T0 freeze / invocation correction — preserved STOP

The `FREEZE.json` and `PLAN.md` for this first construction identity are
preserved exactly as frozen, including the incorrect interpretation of the
image metadata. The read-only inspection command actually returned:

```text
Entrypoint: null
Cmd: ["python3"]
```

The candidate invocation supplied `/work/candidate.py` as Docker's command,
which replaced the image CMD. With no executable entrypoint, the runtime tried
to execute the `.py` file directly and returned `exec format error` before
starting Python. The invocation count is one, but the candidate process never
started; no raw or audit output exists. This is retained as an operator
construction STOP, not a scientific result. Do not edit the frozen metadata,
retry this identity, or treat pre-freeze unit tests as formal output.

The new successor freezes `Entrypoint=null, Cmd=["python3"]` accurately and
uses explicit `--entrypoint python3`; it does not alter or erase this STOP.
