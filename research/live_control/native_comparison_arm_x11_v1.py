"""Custody receipts from the X11 session that actually hosts each comparison arm."""

import json
import os
from pathlib import Path
import stat
import time


CONTEXT_ENV = "AGENT_INTERFACE_NATIVE_COMPARISON_X11_CONTEXT"


def write(path, record):
    temporary = path.with_suffix(".new")
    with temporary.open("x", encoding="utf-8") as stream:
        json.dump(record, stream)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.link(temporary, path)
    temporary.unlink()


def neutral(session):
    return not any(session.d.query_keymap()) and not session.d.screen().root.query_pointer().mask


def guarded_session(base, context, output):
    output = Path(output).resolve()
    raw = Path(context["raw"]).resolve(strict=True)
    relative = output.relative_to(raw)
    if (len(relative.parts) != 3 or relative.parts[0] != "arms"
            or relative.parts[1] not in ("plain", "ephemeral", "persistent")
            or relative.parts[2] != "runtime"
            or Path("/proc/self/cgroup").read_text().strip() != "0::" + context["group"]):
        raise ValueError("runtime session is outside the claimed comparison allocation")
    arm = relative.parts[1]

    class ComparisonSession(base):
        def __init__(self):
            self.comparison_proof = None
            if output.resolve(strict=True) != output:
                raise ValueError("arm evidence directory changed before private X11 startup")
            super().__init__()
            try:
                pids = [self.xvfb.pid, self.openbox.pid]
                lock = Path(f"/tmp/.X{self.display_num}-lock")
                auth = self.auth.resolve(strict=True)
                info = auth.stat()
                group = context["group"]
                if (not 120 <= self.display_num < 190 or self.name == context["outer_display"]
                        or int(lock.read_text()) != pids[0]
                        or not all(Path(f"/proc/{pid}/cgroup").read_text().strip() == "0::" + group for pid in pids)
                        or not auth.is_relative_to(self.tmp) or info.st_uid != os.getuid()
                        or stat.S_IMODE(info.st_mode) != 0o600 or not neutral(self)
                        or not self.d.has_extension("XTEST") or "WAYLAND_DISPLAY" in self.env
                        or "WAYLAND_SOCKET" in self.env):
                    raise ValueError("actual arm private Xvfb identity or neutral input did not verify")
                proof = {
                    "scope": "actual_comparison_arm_display", "arm": arm, "display": self.name,
                    "number": self.display_num, "pids": pids, "lock": str(lock), "lock_pid": pids[0],
                    "xauthority": str(auth), "xauthority_mode": "0600", "xauthority_uid": info.st_uid,
                    "service_unit": context["unit"], "service_group": group, "claim_token": context["token"],
                    "input_neutral": True, "xtest": True, "wayland_present": False,
                    "started_monotonic_ns": time.monotonic_ns(),
                }
                write(output / "comparison-display-start.json", proof)
                self.comparison_proof = proof
            except BaseException:
                self.close()
                raise

        def close(self):
            proof = self.comparison_proof
            self.comparison_proof = None
            final_neutral = False
            try:
                if proof is not None:
                    final_neutral = neutral(self)
            finally:
                super().close()
                if proof is not None:
                    exits = [process.poll() for process in (self.xvfb, self.openbox)]
                    gone = not Path(proof["lock"]).exists()
                    write(output / "comparison-display-end.json", {
                        **proof, "retired": gone and all(type(code) is int for code in exits),
                        "lock_absent": gone, "owned_returncodes": exits, "input_neutral_at_end": final_neutral,
                        "finished_monotonic_ns": time.monotonic_ns(),
                    })

    return ComparisonSession
