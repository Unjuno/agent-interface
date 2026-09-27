"""Capture-bound GTK/X11 observation transport for Issue #2692."""
import hashlib
import json
import os
from pathlib import Path
import time

from Xlib import X, display


def digest(data):
    return hashlib.sha256(data).hexdigest()


def process_start_ticks(pid):
    stat = Path(f"/proc/{pid}/stat").read_text(encoding="ascii")
    rest = stat[stat.rfind(")") + 2:].split()
    return rest[19]


def source_generation(display_name, xid, pid, start_ticks):
    material = f"{display_name}\0{xid}\0{pid}\0{start_ticks}".encode()
    return digest(material)


def effect_reference(observation_id, intent_epoch, region_id, region_sha256):
    material = f"{observation_id}\0{intent_epoch}\0{region_id}\0{region_sha256}".encode()
    return digest(material)


def text_value(value):
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    return "" if value is None else str(value)


def read_window(display_name, xid):
    dpy = display.Display(display_name)
    try:
        win = dpy.create_resource_object("window", int(xid))
        attrs = win.get_attributes()
        geom = win.get_geometry()
        pid_atom = dpy.intern_atom("_NET_WM_PID")
        prop = win.get_full_property(pid_atom, X.AnyPropertyType)
        pid = int(prop.value[0]) if prop is not None and len(prop.value) else None
        wm_class = win.get_wm_class()
        focus = dpy.get_input_focus().focus
        focus_xid = int(focus.id) if hasattr(focus, "id") else int(focus)
        title = text_value(win.get_wm_name())
        return {
            "xid": int(xid), "pid": pid, "title": title,
            "wm_class": list(wm_class or []),
            "map_state": int(attrs.map_state),
            "geometry": [int(geom.x), int(geom.y), int(geom.width), int(geom.height)],
            "focus_xid": focus_xid,
        }
    finally:
        dpy.close()


class LiveTransport:
    def __init__(self, display_name, raw_jsonl, frame_dir, frame_prefix="frames"):
        self.display_name = display_name
        self.display = display.Display(display_name)
        self.raw_jsonl = Path(raw_jsonl)
        self.frame_dir = Path(frame_dir)
        self.frame_prefix = frame_prefix.rstrip("/")
        self.frame_dir.mkdir(parents=True, exist_ok=True)
        self.sequence = 0

    def close(self):
        self.display.close()

    def capture(self, request, trusted_window):
        self.sequence += 1
        capture_id = f"capture-{self.sequence:03d}"
        xid = int(trusted_window["xid"])
        win = self.display.create_resource_object("window", xid)
        before_ns = time.monotonic_ns()
        before = read_window(self.display_name, xid)
        if before["map_state"] != X.IsViewable:
            raise RuntimeError("source window is not viewable")
        if before["pid"] != trusted_window["pid"] or before["title"] != trusted_window["title"]:
            raise RuntimeError("source window identity changed before capture")
        x, y, width, height = before["geometry"]
        rx, ry, rw, rh = request["region_rect"]
        full_data = bytes(win.get_image(0, 0, width, height, X.ZPixmap, 0xffffffff).data)
        covered = rx >= 0 and ry >= 0 and rw > 0 and rh > 0 and rx + rw <= width and ry + rh <= height
        region_data = bytes(win.get_image(rx, ry, rw, rh, X.ZPixmap, 0xffffffff).data) if covered else b""
        after = read_window(self.display_name, xid)
        after_ns = time.monotonic_ns()
        if before["geometry"] != after["geometry"] or before["pid"] != after["pid"] or before["title"] != after["title"]:
            raise RuntimeError("window changed across capture interval")
        start_ticks = process_start_ticks(trusted_window["pid"])
        generation = source_generation(self.display_name, xid, trusted_window["pid"], start_ticks)
        full_sha = digest(full_data)
        region_sha = digest(region_data)
        full_path = self.frame_dir / f"{capture_id}-full.bin"
        region_path = self.frame_dir / f"{capture_id}-region.bin"
        full_path.write_bytes(full_data)
        region_path.write_bytes(region_data)
        effect_ref = effect_reference(request["observation_id"], request["intent_epoch"],
                                      request["region_id"], region_sha)
        receipt = {
            "observation_id": request["observation_id"],
            "intent_epoch": request["intent_epoch"],
            "region_id": request["region_id"],
            "source_window": xid,
            "source_pid": trusted_window["pid"],
            "source_title": before["title"],
            "source_generation": generation,
            "capture_start_ns": before_ns,
            "capture_end_ns": after_ns,
            "focus_xid": before["focus_xid"],
            "focus_stable": before["focus_xid"] == after["focus_xid"],
            "geometry": before["geometry"],
            "region_rect": [rx, ry, rw, rh],
            "coverage": "COMPLETE" if covered and bool(region_data) else "PARTIAL",
            "freshness": "CURRENT",
            "effect_binding": "BOUND",
            "effect_binding_ref": effect_ref,
            "authority_grants": 0,
            "ambiguous": False,
            "full_frame_sha256": full_sha,
            "full_frame_bytes": len(full_data),
            "region_frame_sha256": region_sha,
            "region_frame_bytes": len(region_data),
            "full_frame_path": f"{self.frame_prefix}/{full_path.name}",
            "region_frame_path": f"{self.frame_prefix}/{region_path.name}",
        }
        raw = {"capture_id": capture_id, "surface": request["surface"],
               "request": request, "source_window_snapshot": before,
               "source_generation": generation, "receipt": receipt}
        with self.raw_jsonl.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n")
        return raw
