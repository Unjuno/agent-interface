# Docker Desktop / WSL2 host-container lease clock study

Successor to Issue #3880, limited to Docker Desktop Linux/amd64 with Ubuntu
WSL2 as the host controller. This is not OrbStack-equivalent evidence and does
not consume #3880's reserved seed or formal allocation. It does not run a game,
model, or input.

## Frozen question

Can a WSL2 host `time.perf_counter_ns()` deadline cross into a Docker Desktop
Linux runtime through the production `research/live_control/unix_json_deadline.py`
AF_UNIX JSON client and be conservatively translated into the container's
`research/live_control/lease.py` clock domain without extending authority?

Four timestamps per exchange are H1 (host send), C2 (container receive), C3
(container send), H4 (host receive). For container-minus-host offset theta,
each sample bounds theta to `[C3-H4, C2-H1]`; RTT, order, and interval width are
retained, never hidden by point-estimate rounding. Mapping a host deadline uses
the lower endpoint, so the container deadline cannot be later than the observed
conservative bound permits.

## Provenance frozen before formal

- Main: `f7d5cc8535995db0c36dd85d4b71877503bd0db8`
- `research/live_control/lease.py` SHA-256: `E71F9850D3999A31FCB86C00F9EF7A8BA19BAE8D3A8BDC11BF7BD620817A535F`
- `research/live_control/unix_json_deadline.py` SHA-256: `DECB19099C686EE494FE307C3BF411E61C59E05470319AB80159147D2BD73DE3`
- Docker Desktop Server: `28.5.1`, Linux/amd64
- Existing local `python:3.12-slim` image ID (run by immutable image ID, not mutable tag): `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`
- Production modules are bind-mounted read-only; no network/pull/build in the formal container.

Formal allocation is one process invocation, 120 timestamp exchanges at a
fixed 5-second cadence, then four lease controls: translated live +25 seconds,
expired, translated +31 seconds, and a host authorization with 500ms remaining
subjected to 750ms server-side transport delay. This last control must be
rejected as expired. The full preregistration is Issue #3886.

Construction log: a shared socket created on `/mnt/c` failed with
`OSError: [Errno 95] Operation not supported`; the same socket created in
WSL2's Linux `/tmp` was visible to the host but initially rejected `connect`
with `PermissionError` because the container created it as root. A third
construction using a dedicated WSL2 `/tmp` socket bind mount and matching
container UID/GID passed one production JSON exchange and production Lease
import. No formal sample has been consumed. Formal evidence files remain in
the repository worktree's evidence directory; only the AF_UNIX socket is placed
in an ephemeral WSL2 Linux temporary directory.

Construction and formal artifacts live in a fresh evidence directory. The
independent audit reconstructs every interval and deadline from raw JSONL and
imports neither runner nor server. A PASS is scoped only to this Docker
Desktop/WSL2 configuration; it says nothing about OrbStack or suspend/resume.
