# A03 preservation and safe revalidation

The historical `audit.py` command is not read-only: it overwrites the frozen `results/AUDIT.json`. The historical `build_freeze.py` likewise overwrites `FREEZE.json`. Do not run either directly. The original README and one-shot package are preserved byte-for-byte; the original `SHA256SUMS` continues to identify that historical package.

Use the additive safe entry points:

```powershell
python research/doom/map01_v39_startup_release_order_a01_20261005/audit_readonly.py
python research/doom/map01_v39_startup_release_order_a01_20261005/build_freeze_once.py
```

The audit wrapper emits its result to stdout. The freeze wrapper refuses to run when `FREEZE.json` already exists. `test_preservation.py` checks that invoking these wrappers leaves the frozen audit and freeze byte-identical. Additive safeguards and this note are listed in `SHA256SUMS_V2`.

These safeguards do not rerun the corrected one-shot candidate. They provide only artifact-preservation and audit CLI checks; they do not validate live input, gameplay, or task effect.
