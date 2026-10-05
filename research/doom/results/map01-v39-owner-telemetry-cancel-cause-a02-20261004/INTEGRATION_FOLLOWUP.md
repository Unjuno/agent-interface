# A02 provenance after #7429 owner-version migration

The A02 candidate and its raw/audit were frozen and run against #7429 commit `0f50064a7ea7a69c51cb6751ac313b0c8b5ec9e2`, where the telemetry-preserving implementation was `research/live_control/input_owner_v12.py`. The exact A02 candidate source bytes are in this evidence branch's commit `f5847058846755c5622631758edc7cdfd9bc2b77`; A02's initial package checksums and auditor refer to that historical tree.

While A02 was being delivered, the stacked #7429 branch advanced to `28bfa088c05d8a28ebe040c481e14e23f1aa5b2b`. It resolves the parallel owner-path collision by renaming the telemetry-preserving/cancellation-aware successor to `input_owner_v13.py`, retains the V11 telemetry base, and adds a forced cancel-during-release-sync regression. The source change in that current parent is identical in behavior to the A02 successor; this PR therefore retains A01/A02 as historical evidence and makes no runtime-code delta relative to the latest parent.

Against the exact updated parent tree, the applicable ExecutorV12, ExecutorV13, and cancellation-publication suites were run locally and passed 15/15. That includes the integrated cancellation-during-sync regression. This is host-side fake-Xlib software testing only; the absent local `python:3.14` image prevented a container run. No live allocation or game/model/input was used.

`audit_history.py` verifies the saved A02 raw, original audit receipt, both original package manifests, and the historical candidate source from its pinned commit without rerunning the candidate. Run it from the repository root with `python3 -B research/doom/results/map01-v39-owner-telemetry-cancel-cause-a02-20261004/audit_history.py`.
