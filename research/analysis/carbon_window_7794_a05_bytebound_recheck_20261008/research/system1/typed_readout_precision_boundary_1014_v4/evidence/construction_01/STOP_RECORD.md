# STOP record — Issue #4912 construction_01

**STOP_DOCKER_CLI_USAGE_ERROR before container creation.** The host wrapper invoked `docker` followed immediately by Docker run flags and omitted the `run` subcommand. Docker exited 125 with `unknown flag: --rm`. No container was created, the frozen runner did not start, and no model load or forward, corpus read, precision measurement, formal row, or training occurred. No retry was made; this allocation remains consumed. This is an invocation STOP, not a scientific result.

Raw output is empty. Captured stdout is 0 bytes (SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`). Captured stderr is 109 bytes (SHA-256 `12bdcf916ade656d8940d40bc2efc62f8ed0a543cc19916b2585f81ba6176dda`). The host receipt records exit 125. RTX 3080 was 0% / 0 MiB after the attempt. Resident Ollama and X11 diagnostic containers were left untouched.

`audit_stop.py` independently checks the retained CLI error, receipt, absent raw files, no candidate container in the Docker snapshot, and idle post-attempt GPU. The v4 preregistered precision gates and source remain unchanged; this STOP does not support or refute the numerical hypothesis.