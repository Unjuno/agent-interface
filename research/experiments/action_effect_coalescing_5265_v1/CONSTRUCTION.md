# Construction log (pre-freeze)

Host: Ubuntu 24.04 in WSL2; CPython 3.12.3; standard library only. No dependency installation, container, network call, model, GUI, or input was used.

## Preserved invocation failure

Command attempted through the Windows-to-WSL shell boundary:

```text
python3 -B -m unittest discover -s . -p 'test_*.py' -v
```

Observed result: unittest exited nonzero before collecting tests and reported `ImportError: Start directory is not importable: 'test_coalescing.py'`. No test method ran. The shell-boundary parsing cause was not isolated; this is retained as an invocation failure, not classified as a code/test failure.

## Corrected construction command

```text
python3 -B -m unittest -v test_coalescing test_audit
```

Exit 0; **20/20 tests passed**. This includes 13 candidate-behavior tests and 7 independent-audit/mutation tests. Exact stdout was observed in the task terminal; the compact transcript is retained here. A no-write built-in `compile()` check over all package `*.py` files also printed `compile: PASS`.

These are pre-freeze construction checks only. They are not the one-shot formal run or its separate raw audit.
