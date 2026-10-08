# STOP before candidate — allocation 01

At the immediate launch gate on 2026-10-01, the GitHub `main` ref had advanced from frozen `7e94ba9fdbfbff8d32d5dde27c086f2eb7582775` to `443bcb63333c4614d9a6fee5cb3ca3f9f6ea9710`. The preregistered gate required a stop/refreeze on any main movement. No candidate or auditor container ran; no raw scientific result exists. This is `STOP_MAIN_ADVANCED_BEFORE_CANDIDATE`, not a method failure or pass.

The cloned task guest `obs-5776-probe-intervention-t1-20261001-01` (machine ID `01M3V3YWYGT8S7QRW7Y6B9H54K`) was stopped at the gate. A shared OrbStack Docker container belonging to another task was observed live and left untouched. The start-gate STOP and a new non-overlapping allocation request are recorded on [#5085](https://github.com/Unjuno/agent-interface/issues/5085#issuecomment-5926386417) and [#5776](https://github.com/Unjuno/agent-interface/issues/5776#issuecomment-5926386700).

The 4/4 host tests were construction checks only. The new probe-intervention hypothesis remains untested; this package must not be presented as its experiment result.
