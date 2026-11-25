# Windows Codex executable candidate

Golden Desktop v3 runs inside WSLg with the Linux/X11 Chromium backend. This candidate adds an explicit alternative for the Windows Codex bridge while keeping the same GUI host, launchers, schema gate and release acceptance requirements.

The default bridge uses Windows Node to run `codex.js`. The setting `AGENT_INTERFACE_WINDOWS_CODEX_EXE` selects an absolute WSL path to an existing Windows `.exe`. Set `CODEX_HOME` to the corresponding existing WSL directory visible to the Windows process. The bridge forwards that directory through `WSLENV` to both the Windows Python preflight and the native App Server. Windows Python is still needed for schema preflight. Native selection requires the built-in preflight runner. The configuration examples below name local files and perform no installation.

```bash
export AGENT_INTERFACE_WINDOWS_CODEX_EXE='/mnt/c/path/to/codex.exe'
export CODEX_HOME='/mnt/c/path/to/Windows/Codex/home'
./runtime/golden-demo-v3.sh doctor
```

Doctor runs the selected Codex binary with `--version`. It also checks the Linux browser launcher with a bounded `--version` call before schema preflight can run. A Linux wrapper such as `/usr/bin/google-chrome` is supported. A Windows `.exe` is outside this Linux/X11 browser path. Fresh execution sends the native path to the existing persistent App Server launcher and invokes the same Windows schema runner with a native `codex exec` prefix. The latter keeps its read-only sandbox, output schema, instructions, feature restrictions and no-retry boundary. Native schema cache entries bind the executable SHA-256, version and runner SHA-256. The older Node+JS identity keeps its existing fields, and the runner source change invalidates any previous cache key using that file.

An offline Ubuntu WSL2 probe used the installed Windows binary `codex-cli 0.171.0-alpha.13.2` (SHA-256 `2a1ec3f1dd463fd30224be4c0c67d3fe83d3d863a3d7539ccad366952436d2aa`). A temporary Windows-visible `CODEX_HOME` with a loopback model endpoint and analytics disabled isolated the App Server. `initialize` returned the Windows platform and the expected temporary home. The only outbound methods were `initialize` and `initialized`. Closing stdin produced exit code 0. The installed binary's generated schema includes local-image inputs, output schemas and the turn usage notification, with `cacheWriteInputTokens` declared optional. The candidate refuses missing accounting at the schema gate or grounding call and preserves the raw evidence. Endpoint behavior and the live Golden workflow remain unverified.

The historical RC1 freeze, frozen source archive and prior evidence remain separate. A future supported-host acceptance must use the selected native configuration, retain fresh evidence and complete its own audit. No model, application input or dependency download was used for this offline check.


The same offline run confirmed that the installed Windows Python received both the converted executable path, including spaces, and the same temporary `CODEX_HOME`. Golden runtime and acceptance tests passed 30/30 on Python 3.13 in both normal and `-O` modes. Release archive tests passed 6 with 1 Windows-specific skip in each mode. The retained audit matched all 29 archived sources.
