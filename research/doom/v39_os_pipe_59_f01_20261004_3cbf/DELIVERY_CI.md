# F01 saved-only delivery CI

Commit cbfa03539, own VM research-6183-t0-20261003.
Fixed host/guest Git archive SHA256 both:
76cca9dbde759757912d12b401f0a09687cab42e852fbfc662a2c2e4acbd5e2a.
Image sha256:560af28c711a2bf94cf9bedef4f5e47b26f86ea5bc79211c603addb74237540b.
Container f01-saved-check-v1 configured netnone/UID501/CPU1/1GiB/swap0/pids128/
read-only/capdropALL, isolated64MiBtmpfs. No producer/child/reader rerun.

Command python3 -B -O -W error -m unittest discover -v && python3 -B verify_saved.py.
Retained result:3tests,0.001s,OK; PASS_PARSER_NOTIFICATION_EOF_UNRESOLVED.
Source/outcome/childliveness/cleanup and invalidclock/retry aliases rejected by
negative controls; immutable summary anchor/exact5fileinventory/cellcopies pass.
This is delivery verification, not new formal experiment or independent review.

Docker State:
```
{"Status":"exited","Running":false,"Paused":false,"Restarting":false,"OOMKilled":false,"Dead":false,"Pid":0,"ExitCode":0,"Error":"","StartedAt":"2026-10-03T22:48:42.771170491Z","FinishedAt":"2026-10-03T22:48:43.030145926Z"}
```
