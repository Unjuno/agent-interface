# Construction receipt — not formal

- Candidate construction command: python3 candidate.py
- Independent auditor construction command: python3 auditor.py
- Suite: python3 test_method.py
- Syntax: python3 -m py_compile coder_a.py coder_b.py candidate.py auditor.py test_method.py
- Input parsing: python3 -m json.tool traces.json; python3 -m json.tool key.json
- Result: PASS construction assertions=16; 4 mutation controls rejected; 24 rows across 4 scenarios reconstructed; audit errors=[].
- Runtime: host CPython 3.14.5. This receipt does not claim Docker/OrbStack execution.
- Formal allocation candidate/auditor invocations: 0/0; retries: 0.
- Slot status: requested, not granted. No container was launched.
- Construction failures: see FAILURE_CONSTRUCTION_01.txt.

Formal commands must be run only after exact-source freeze and explicit shared
CPU slot grant. Candidate is one-shot; auditor runs once only if candidate
exits 0. Do not rerun a consumed formal allocation.
