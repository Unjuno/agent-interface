# Current-main WSL Chrome configuration diagnostic R04

**Disposition: acceptance HOLD; one doctor configuration check advanced.** This diagnostic tested whether an already-installed Windows Chrome executable can be presented to the frozen WSL doctor through its documented environment override. It did not launch Chrome or exercise the browser bridge.

## Frozen source and host

- Source revision: `c5fc0ee00b5fa5208088ee69004a336770336ac4`.
- Ubuntu WSL2, Python 3.12.3; persistent full checkout under `/home/user`.
- Windows Chrome file: `C:\Program Files\Google\Chrome\Application\chrome.exe`, version `157.0.8103.79`, 4,149,912 bytes. The file is visible and marked executable at `/mnt/c/Program Files/Google/Chrome/Application/chrome.exe` from WSL.
- The frozen doctor defaults to `shutil.which("google-chrome")`; an explicit `AGENT_INTERFACE_CHROMIUM` value overrides this lookup. The test set that variable only for the one doctor subprocess.

## Result

- `runtime/golden-demo-v3.sh doctor` with `AGENT_INTERFACE_CHROMIUM=/mnt/c/Program Files/Google/Chrome/Application/chrome.exe` passed 9/15 checks, versus 8/15 in default R03; the `chromium` path-presence check changed to pass.
- Six checks still fail: Python `PIL`, `numpy`, `openpyxl`, `et_xmlfile`; `windows_cli`; and `codex_cli`.
- Overall doctor remained `passed: false` and exited 1. The doctor only checks that the configured Chrome path exists; this does not prove the browser launches, that it can connect to WSL X11, or that the runtime can control it.
- No dependency, browser, CLI, model, or runtime was installed or downloaded. Chrome was not launched; no GUI, provider, task allocation, or input action occurred.

The default R03 `chromium: null` was a discovery/configuration gap, not absence of Windows Chrome. The actual Windows-to-WSL browser path remains unqualified. #58 remains open; no Research Preview acceptance claim follows.

## Raw custody

- `raw/doctor.stdout.json`, `raw/doctor.stderr.txt`, `raw/doctor.exit_code.txt`: exact R04 doctor output.
- `raw/SHA256SUMS`: hashes for the captured files.
- R03 retains the first acceptance-run output and default doctor response.
