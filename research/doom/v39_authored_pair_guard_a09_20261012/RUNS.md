# A09 execution record

One local Windows preflight and one frozen WSLc container invocation ran. The WSLc invocation ran once:

```text
wslc run --rm --network none --cpus 1 --memory 512m a09-authored-pair-guard:20261012
```

Both invocations exited 0 (the Windows preflight under CPython 3.11.9; WSLc under CPython 3.14.8). Their summaries are preserved separately in `results/local_preflight.stdout.txt` and `results/wslc.stdout.txt`; `results/exit.txt` retains the WSLc exit status. WSLc image identity and build details are in `FREEZE.json`; `results/environment.txt` records the separate, non-test cgroup probe and swap-limit warning. No optimized-mode test was run.

The test AST-extracts controller definitions from the frozen source files and instantiates the real `ObservableSignalGuard`. Its values and bindings are synthetic. `audit_a09.py` checks source Git blob IDs, byte counts and SHA-256 plus the retained raw transcript; it does not rerun tests.
