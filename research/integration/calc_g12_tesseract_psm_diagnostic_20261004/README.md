# G12 known-crop Tesseract segmentation diagnostic

Five segmentation modes read the exact retained G12 OCR crop as `551` on the
local macOS Tesseract 5.5.2 installation. PSM 7 on this host returned `551`,
while the original G12 WSLc image returned `951` on the same SHA256-identical
crop. This establishes an environment-dependent discrepancy for one known
image; it does not identify which environment component caused it.

| PSM | Output | Exit | Elapsed |
|---:|---|---:|---:|
| 6 | `551` | 0 | 118.556 ms |
| 7 | `551` | 0 | 103.224 ms |
| 8 | `551` | 0 | 93.881 ms |
| 10 | `551` | 0 | 93.235 ms |
| 13 | `551` | 0 | 97.211 ms |

The input is copied byte-for-byte from PR #7198’s retained G12 crop:
SHA256 `851ad8686d681fe55aaa6ac8c609e67f47812334d8ded79658434e94ff8445f8`,
392×96 pixels. The G12 crop visibly contains `551`, while its original PSM 7
OCR attempt returned `951`. On this Mac, PSM 7 control and four alternative
modes all returned `551` with the same language and digit whitelist. The
G12 runner did not retain Tesseract’s version string, so version, build,
linked libraries, and platform remain competing explanations.

## H / T / D / C / U

- **H:** PSM choice may explain some of the G12 known-crop recognition error.
- **T:** One OCR call at each frozen mode 6, 7, 8, 10, and 13, holding the crop,
  Tesseract binary, English language, and digit whitelist fixed.
- **D:** Any exact `551` result identifies a mode candidate for later
  validation. All five modes matched on this host.
- **C:** The same-image result may fit this known label. The G12 run used a
  different pinned image/environment, so this does not isolate PSM or software
  version as the cause.
- **U:** One known image and one call per mode; no held-out recognition, live
  application, task-completion, or efficiency claim.

This is a post-run saved-image diagnostic, not a new GUI/model allocation and
not a G12 regrade. G12 remains `HOLD_OCR_FALSE_NEGATIVE_CONTINUATION_UNEXERCISED`;
its second save remains censored. The independent raw check reports
`PASS_RAW_INTEGRITY_SCOPED` in `AUDIT.json`.

## Reproduction and audit

The one-shot runner and input hash were frozen in `FREEZE.md` before the calls.
The exact command was:

```sh
python3 research/integration/calc_g12_tesseract_psm_diagnostic_20261004/run_diagnostic.py
```

It writes `RAW.json` once and refuses to overwrite an existing result. The
read-only auditor command is:

```sh
python3 research/integration/calc_g12_tesseract_psm_diagnostic_20261004/audit_raw.py
```

The auditor checks input bytes/hash, mode inventory, argv equality except for
PSM, exits, exact outputs, version record, and monotonic intervals. It does not
establish OCR accuracy beyond this saved crop.

Corruption control: a temporary copy with the PSM 7 stdout changed to `951`
was rejected with exit 1 and errors for both the output and disposition
consistency. The committed `RAW.json` was not modified by that control.

The next discriminating validation should record the Tesseract version from
inside the candidate pinned container and test a preregistered digit panel on
newly rendered captures. Do not tune on this crop and then call the same crop
held out.
