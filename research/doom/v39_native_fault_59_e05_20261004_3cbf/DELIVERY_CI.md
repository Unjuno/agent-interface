# Saved-only delivery CI at 64e6e30c5

Fixed Git archive host and private guest SHA256 both:
1b75824dbfb75baf48f8d097fa986226b23f3e5fc34223e4600d2bce64ab65ae.
Private VM research-6183-t0-20261003, frozen image560af28c…37540b.
Container e05-delivery-ci-64e6e30c5, UID501/networknone/CPU1/memory1GiB/
swap0/pids128/read-only/capdropALL, isolated tmpfs. Exact committed package
mounted read-only, not the native allocation. No game or official auditor run.

Command: python3 -B -O -W error -m unittest test_delivery &&
python3 -B verify_delivery.py

Retained stdout/stderr:
```
...
Ran 3 tests in 0.025s
OK
{"delivery": "VERIFIED_FIRST_AUDIT_ANCHOR", "files": 73, "scope": "retained delivery only; no producer or official auditor rerun"}
```

Docker State receipt:
```
{"Status":"exited","Running":false,"Paused":false,"Restarting":false,"OOMKilled":false,"Dead":false,"Pid":0,"ExitCode":0,"Error":"","StartedAt":"2026-10-03T22:37:48.706034884Z","FinishedAt":"2026-10-03T22:37:49.000301834Z"}
```

This is the three delivery controls only, not the earlier34-method construction
CI, independent result review, GitHub CI or production-adoption approval.

## Full revised delivery CI at daaf4a7b3

After independent READY and receipt-anchor repair, fixed Git archive included
E05 plus unchanged E03 private-fixture dependency. Host/guest SHA both
cbd3dbbcd009b682fc5142073a7a218835baeb651d603460beb31392f3787c27.
Container e05-full-delivery-ci-daaf4a7b3 used the same frozen image and limits,
read-only packages, networknone and isolated256MiBtmpfs.
Command python3 -B -O -W error -m unittest discover -v &&
python3 -B verify_delivery.py: 38tests,1.152s,OK; delivery VERIFIED_FIRST_AUDIT_ANCHOR,
73files. Includes actual Xvfb close boundaries and exact AST receiver controls,
private partial STOP test fixtures only; no consumed producer/officialaudit run.
Docker State receipt:
```
{"Status":"exited","Running":false,"Paused":false,"Restarting":false,"OOMKilled":false,"Dead":false,"Pid":0,"ExitCode":0,"Error":"","StartedAt":"2026-10-03T22:41:27.131862729Z","FinishedAt":"2026-10-03T22:41:28.729981558Z"}
```
