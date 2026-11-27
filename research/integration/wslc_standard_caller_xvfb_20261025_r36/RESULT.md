# R36 — pre-run stop: Windows line endings in container script

**Disposition: STOP_PREINPUT, no Xvfb or test input.** The container was isolated and the staged interpreter ran, but Python could not open the runner path because the mounted shell script had CRLF line endings; the trailing carriage return became part of the filename. The caller test body did not start.

R36 produced no Xvfb or input. Its exact container was removed and verified absent. R37 writes the container-init shell script with LF line endings before its single attempt. R36 is not retried.
