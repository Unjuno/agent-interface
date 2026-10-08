# Issue #2849 saved-response pipeline confirmation v28

No-task offline replay of the exact v26 Codex response. Reuses the unchanged v27 corrected nested runner, while the outer harness inherits the repository root on `PYTHONPATH` so the unchanged selected backend can import its schema validator. One network-disabled outer and one network-disabled nested container; no host model or task runtime.
