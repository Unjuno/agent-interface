# Correction: complete #4988 host captures

The merged #5016 STOP record remains unchanged. Its committed `preflight.txt` and `postflight.txt` contain literal `Warning: truncated output` markers inserted by a bounded tool-output capture; they are not complete raw observations and should not be used to substantiate the omitted process/container rows.

These two files are byte-for-byte copies of the complete host-side captures recovered from the original #4988 workspace. Their SHA-256 digests and byte lengths are:

- `preflight.full.txt`: 5672 bytes, SHA-256 `f2cdfb65bf69ddf327e86662fe235d80af29e8be76acdad248a83e2cc4e82512`
- `postflight.full.txt`: 4656 bytes, SHA-256 `7872a53bfbc21aeacfa1164d9e687f4c87689c66393bae6767ec6e6c60e65035`

The captures show the GPU at 0 MiB / 0% both before and after the failed preflight invocation. The postflight capture includes the full container/process listing. This is a documentation correction only: no experiment was rerun, no model fit occurred, and the original main-branch files/history were not altered.