# A02 pre-freeze construction outcomes

These outcomes occurred before the A02 allocation freeze and were not counted
as candidate/baseline runs. They are retained to explain the fixture revisions.
The source files were not frozen for these construction attempts, so these logs
are diagnostic history only and are excluded from the A03 audit.

## C01 — harness could not steal foreground

Command: `python -m unittest runtime.backends.win32_v1.test_focus_drift.NativeForegroundFenceTests -v`

The attempt called `SetForegroundWindow(decoy)` from the test harness after the
target fixture became foreground. Windows denied the switch; the foreground
remained the target. This prompted the target's own message loop to request the
switch in later construction.

```text
test_native_focus_change_after_focus_refuses_before_sendinput ... FAIL

AssertionError: Lists differ: [{'set_foreground_returned': False, 'foreground': 36440476}] != [{'set_foreground_returned': True, 'foreground': 96339878}]

Ran 1 test in 0.836s

FAILED (failures=1)
```

## C02 — decoy metadata was not ready

The second construction started the target before waiting for the decoy fixture
metadata. It stopped in setup before the test or backend dispatch ran.

```text
test_native_focus_change_after_focus_refuses_before_sendinput ... ERROR
File "runtime/backends/win32_v1/test_focus_drift.py", line 186, in setUp
  str(json.loads(decoy_meta.read_text())["hwnd"]),
FileNotFoundError: [Errno 2] No such file or directory: '<temp>\\decoy\\meta.json'

Ran 1 test in 0.020s

FAILED (errors=1)
```
