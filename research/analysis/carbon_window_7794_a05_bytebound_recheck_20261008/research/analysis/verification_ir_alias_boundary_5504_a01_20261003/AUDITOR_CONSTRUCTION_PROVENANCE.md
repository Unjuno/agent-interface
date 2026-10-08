# Independent construction launcher provenance

The independent author ran exactly audit-red-01 and audit-green-01 using
capture v1 in the shared package directory, not a mirror or relocated script.
The receipt argv records the unittest child only. Main noticed that its source
hash map lacked producer files and requested clarification before freeze.
The author disclosed the outer launcher's in-memory Path.glob filter below.
On-disk capture source was unchanged; this is an execution setting omitted
from the original receipt, not a complete package source manifest.

```powershell
python -B -c "from pathlib import Path; import runpy; audit_capture_glob = Path.glob; Path.glob = lambda self, pattern: (path for path in audit_capture_glob(self, pattern) if path.name in ('audit.py', 'test_audit.py', 'capture_run.py')); runpy.run_path('capture_run.py', run_name='__main__')" --output construction/audit-red-01 --purpose independent-auditor-construction-RED-absent-implementation --timeout 30 -- python -B -m unittest -v test_audit

python -B -c "from pathlib import Path; import runpy; audit_capture_glob = Path.glob; Path.glob = lambda self, pattern: (path for path in audit_capture_glob(self, pattern) if path.name in ('audit.py', 'test_audit.py', 'capture_run.py')); runpy.run_path('capture_run.py', run_name='__main__')" --output construction/audit-green-01 --purpose independent-auditor-construction-GREEN-fixtures-only --timeout 30 -- python -B -m unittest -v test_audit
```

Cwd was this package at the absolute checkout path recorded in both receipts.
Python resolved to C:\Users\junny\AppData\Local\Programs\Python\Python312\python.exe,
3.12.10, Windows, no environment overrides. The filter ran only in the capture
parent, before hash read_bytes(), excluding modelchecker.py/test_modelchecker.py
to keep the independent author's strict no-producer-read boundary. The unittest
child used a new interpreter and did not inherit the filter. RED lacked
audit.py; GREEN included it. Recorded wrapper hash matches the inert v1 source.

This retrospective explanation comes from the author and is not independently
authenticated command history. First receipts/streams are preserved unchanged.
Main's fresh combined pre-freeze-green-01 used direct capture v2 with no filter,
and records all six package Python sources. Formal execution also uses direct
capture v2, no runpy/monkeypatch/filter/launcher override. Source hashes alone
cannot prove absence of runtime monkeypatches; outer commands and receipts
must be read together. No construction record is promoted to formal evidence.
