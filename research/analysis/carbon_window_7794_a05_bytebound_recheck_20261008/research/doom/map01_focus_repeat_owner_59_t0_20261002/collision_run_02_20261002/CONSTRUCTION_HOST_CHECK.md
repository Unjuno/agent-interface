# Host-only construction check — 2026-10-02

After the formal allocation, an extra, non-frozen host check was attempted with Windows host Python 3.11:

```text
python -B -m unittest discover -s . -p 'test_*.py' -v
```

It exited 1 before executing tests. `test_audit.py` could not import `Xlib` (`ModuleNotFoundError`; the Windows host does not have the pinned image's `python-xlib`). The package-level import in `test_process_boundary.py` also could not resolve `research` under this package-directory invocation. This host check is not the preregistered environment and does not alter the already completed one-shot candidate/auditor result. No dependency was installed and no retry was made. The frozen pre-formal WSLc construction suite remains 28/28 PASS on the exact dedicated image.
