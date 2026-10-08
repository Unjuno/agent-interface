from __future__ import annotations

from pathlib import Path

from Xlib.ext import res


def process_start_ticks(pid: int) -> str:
    fields = Path(f"/proc/{pid}/stat").read_text(encoding="ascii").split()
    return fields[21]


def owner_identity(d, xid: int, start_reader=process_start_ticks) -> dict:
    version = d.res_query_version()
    if (version.server_major, version.server_minor) < (1, 2):
        raise RuntimeError("XRes client identity version < 1.2")
    mask = res.ClientXIDMask | res.LocalClientPIDMask
    reply = d.res_query_client_ids([{"client": xid, "mask": mask}])
    rows = []
    for value in reply.ids:
        client = int(value.spec.client)
        value_mask = int(value.spec.mask)
        pids = [int(pid) for pid in value.value] if value_mask & res.LocalClientPIDMask else []
        rows.append({"client_xid": client, "mask": value_mask, "local_pids": pids})
    candidates = [row for row in rows if row["client_xid"] == xid
                  and row["mask"] & res.LocalClientPIDMask]
    if len(candidates) != 1 or len(candidates[0]["local_pids"]) != 1:
        raise RuntimeError("XRes did not return one local process identity")
    pid = candidates[0]["local_pids"][0]
    if pid <= 0:
        raise RuntimeError("XRes returned invalid local PID")
    start_ticks = start_reader(pid)
    if not start_ticks:
        raise RuntimeError("process start identity unavailable")
    return {"xid": xid, "pid": pid, "pid_start_ticks": str(start_ticks),
            "xres_version": [version.server_major, version.server_minor],
            "xres_rows": rows}


def permits(captured: dict, current: dict) -> tuple[bool, str]:
    required = ("xid", "pid", "pid_start_ticks")
    if any(key not in captured or key not in current for key in required):
        return False, "IDENTITY_INCOMPLETE"
    if any(captured[key] != current[key] for key in required):
        return False, "PROCESS_INCARNATION_MISMATCH"
    return True, "SAME_PROCESS_INCARNATION"
