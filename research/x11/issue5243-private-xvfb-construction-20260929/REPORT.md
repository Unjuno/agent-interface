# Construction-01 result — retained STOP

Disposition: `STOP_XVFB_CLEAN_TERMINATION_AND_AUDIT`.

The four CPU-only construction tests passed before the probe. Exactly one
private-Xvfb probe was launched from the frozen candidate; it sent no fixture,
XTEST, HID or other application input and used no Docker/OrbStack, network,
GPU or model.

## Observations

- Host mount namespace inode `4026532400`; child inode `4026532414`.
- Child mountinfo showed a `tmpfs` exactly at `/tmp/.X11-unix`, mode `01777`.
  Linux mountinfo reported source `none` for this tmpfs mount.
- Xvfb `:97` reached ready; Xlib connected and read `640x480`; private X socket
  existed.
- Host WSLg socket directory stayed mode `0777`, inode `2`, device `84` before
  and after. A subsequent process check found no remaining Xvfb process.
- Xvfb did not terminate within the frozen 3-second graceful-shutdown wait
  after SIGTERM; the runner needed SIGKILL. Its status was `-9`; wrapper status
  was `2`. This is a lifecycle STOP, not a pass.
- The frozen raw auditor was invoked once and exited `1` with
  `ValueError: wrapper exit/timeout`. It therefore did not issue a PASS; no
  audit retry or source repair was made. Its pre-probe test suite had exercised
  five corruption mutations, all rejected, but synthetic controls do not turn
  this raw audit into a pass.

The exact `result.json`, `child-record.json`, `xvfb.log`, auditor stdout/stderr
and exit code are retained in `results/construction-01/`. No formal allocation
or XTEST row was launched. Any changed shutdown/audit implementation requires a
distinct successor freeze; the consumed probe is not rerun.

## SHA-256 of retained raw files

```text
result.json      FB78D27CF2FA81785A7A8B84404F797EADED63333ED9275BD25572707EBF21D5
child-record.json 7F397B6FF2E15C085EB1B1B65DE40E7319C28336E09B7BC6D77DD6E1DC332353
xvfb.log        12DCABF0449B9FF85D589B86D110C814777977DACA56E7BA8EC300C5334FE397
audit.stderr    4036C8B9E57DB89D6C75E5A348BF05D530E9A6ED84A1C89CF3E1B18E1987A00D
audit.exitcode  01BA4719C80B6FE911B091A7C05124B64EEECE964E09C058EF8F9805DACA546B
```
