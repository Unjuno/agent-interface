# Reused pinned venv supported-host diagnostic R06

## Result

On current main 7e9caab2acf8428beeb48682edd5e7a0bace4967, the preserved R05 Ubuntu WSL virtual environment was reused without package installation. Its nine installed packages and the current main requirements file have identical pins and matching file SHA-256 1065afbce7e148dfb1a736cba251b81620898adc274761e411262ca4742341d3.

The current-main doctor ran with AGENT_INTERFACE_CHROMIUM set to the existing Windows Chrome executable path. It reported 13/15 checks passed: all Linux/WSLg, X11 connection, Python imports, Windows Python/Node paths, and Chrome path checks passed. Only windows_cli and downstream codex_cli failed because the expected Windows Codex CLI JavaScript entrypoint is absent. Chrome was not launched. The direct doctor result is HOLD and returned exit 1, confirmed by a parent subprocess capture.

The shell wrapper for the first doctor invocation recorded exit code 0 even though the JSON reported passed=false. Preserve raw/exit-code.txt as a wrapper-capture deviation; raw/doctor-parent.exit-code.txt is the independently captured process status 1 and controls interpretation.

The current-main retained audit passed with disposition RETAIN: 29 frozen sources validated; one recorded three-arm, 18-task allocation was reconstructed. It is historical retained evidence and does not satisfy a fresh golden task or live acceptance.

## Scope limits

No package/runtime/browser/model was installed. There was no model/provider call, Chrome launch, GUI input, fresh golden run, Docker/WSLc use, or live allocation. Research Preview acceptance and graduation remain open pending the exact Windows Codex CLI JS entrypoint, fresh no-retry run, and independent audit-live.

## Custody

Conditions and all raw stdout/stderr/exit receipts are in this directory. SHA256SUMS covers the complete packet.
