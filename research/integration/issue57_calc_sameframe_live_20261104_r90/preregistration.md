# Preregistration: Calc current-source, saved-effect, and container-exit gate r90-a01

Freeze: 2026-11-04, before the sole live attempt. This is a new attempt after r89-a01's task and lifecycle gates passed but its Docker run returned 127 because the Bash runner had a CRLF trailing blank line. It tests the same candidate implementation (`8c4de6f73789230d20c1400cb0c97ff8497d303a`) from the PR branch, whose ten relevant source-file hashes are frozen in `source-freeze.json`. The current evidence checkout contains r89 artifacts; implementation sources are byte-identical to the candidate hashes. Attempt ID `issue57-r90-a01`. One fresh Docker/Xvfb container and one registered Calc task; no retry or replacement under this registration.

## Question and gate

Does the guarded Calc path on the candidate code prove A1=731/A2=864, verified release after both input transitions, same-frame Save request/effect linkage, identical frozen task crop across final accepted observations, independently verified saved FODS, clean exact Calc generation exit, parent post-close verification, and Docker exit code zero?

`PASS_SCOPED` requires every gate in the frozen `audit.py`; any false or unknown gate is `FAIL_OR_UNKNOWN`. The rectangle is `(left=0, top=126, right=1218, bottom=742)` in RGB; right/bottom are exclusive. r89 passed this crop gate once, so r90 is a second prospective check, not broad reliability evidence. No threshold is relaxed. No second r90 run is allowed.

## Frozen environment and procedure

Use only cached image `sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425`, no image pull/build. Docker Engine 29.8.1, Desktop 4.93.0. Host `.wslconfig` 24 GiB memory, 12 processors, 8 GiB swap, gradual reclaim. Live container limits 2 CPUs, 4 GiB memory and swap total, 256 PIDs. Source mount read-only; only this packet is writable. Bridge networking is used only for exact Debian packages: LibreOffice `4:7.4.7-1+deb12u14`, Tesseract `5.3.0-2`. No provider/model/API generation, WSLc, MAP01, image pull/build/prune, other desktop target, or host data write.

`runner.sh` was normalized bytewise to LF and verified to contain no CR bytes before freeze. `run-live.ps1` records Docker stdout and `$LASTEXITCODE` immediately after the single `docker run`, including nonzero results. The offline `run-audit.ps1` separately captures audit exit. The image remains pinned and the container uses `--rm`.

## Interpretation

This is one candidate-branch Calc trial only. Even `PASS_SCOPED` does not establish a speedup (there is no matched conventional arm), broad reliability, integrated recovery, WSLc, MAP01, or product completion.
