"""Capture fixed synthetic relevance pairs from real Xvfb X11 drawable bytes."""
import hashlib
import json
import os
import struct
import time
import tkinter as tk
import zlib
from pathlib import Path

from Xlib import X, display
from Xlib.protocol import request

OUT = Path(os.environ["OUT_DIR"])
W, H = 320, 240
FAMILIES = [
    {"bg": "#f2eee8", "panel": "#fffdf9", "ink": "#30353b", "accent": "#c35a37"},
    {"bg": "#e8f4f1", "panel": "#fbfffd", "ink": "#233b36", "accent": "#117c70"},
    {"bg": "#f3eafa", "panel": "#fffaff", "ink": "#39234a", "accent": "#9a4ac2"},
    {"bg": "#f6f0d8", "panel": "#fffcee", "ink": "#3f3822", "accent": "#b47a12"},
    {"bg": "#182b24", "panel": "#274538", "ink": "#edf7ef", "accent": "#91c847"},
    {"bg": "#2b2033", "panel": "#44304f", "ink": "#fbecff", "accent": "#ef7ce3"},
    {"bg": "#e4eaf7", "panel": "#f9fbff", "ink": "#263555", "accent": "#375bdd"},
    {"bg": "#f7e6df", "panel": "#fff8f4", "ink": "#4a2922", "accent": "#d15030"},
]
LAYOUTS = [
    ((12, 18, 308, 222), (38, 52, 152, 124), (205, 158, 290, 205)),
    ((24, 12, 296, 228), (158, 34, 274, 110), (42, 158, 131, 204)),
    ((16, 28, 304, 212), (56, 126, 176, 195), (192, 46, 280, 94)),
    ((28, 10, 292, 230), (132, 42, 269, 116), (44, 165, 122, 215)),
    ((10, 24, 310, 216), (42, 92, 156, 166), (196, 48, 282, 96)),
    ((20, 16, 300, 224), (164, 120, 280, 194), (42, 44, 126, 92)),
    ((12, 12, 308, 228), (34, 54, 169, 126), (202, 152, 292, 204)),
    ((18, 18, 302, 222), (150, 100, 278, 176), (40, 42, 124, 96)),
]


def digest(b):
    return hashlib.sha256(b).hexdigest()


def wait_idle(root):
    root.update_idletasks()
    root.update()
    time.sleep(0.035)
    root.update_idletasks()
    root.update()


def draw(root, family, roi, kind, variant, state):
    f = FAMILIES[family]
    c = root.canvas
    c.delete("all")
    c.configure(background=f["bg"])
    box, task, critical = LAYOUTS[family]
    # Draw a source window with a family-specific geometry and stable task/critical regions.
    c.create_rectangle(*box, fill=f["panel"], outline=f["accent"], width=3)
    c.create_text(box[0] + 16, box[1] + 14, anchor="nw", text=f"Workspace family {family}", fill=f["ink"], font=("TkDefaultFont", 10, "bold"))
    c.create_rectangle(*task, fill=f["bg"], outline=f["ink"], width=2)
    c.create_text(task[0] + 6, task[1] + 4, anchor="nw", text="TASK VALUE", fill=f["ink"], font=("TkDefaultFont", 9))
    c.create_rectangle(*critical, fill=f["accent"], outline=f["ink"], width=1)
    c.create_text((critical[0] + critical[2]) // 2, (critical[1] + critical[3]) // 2, text="LOCK", fill=f["panel"], font=("TkDefaultFont", 8, "bold"))
    # The changed tile is either outside task/critical, inside task, or in critical ROI.
    if kind == "irrelevant":
        # Deterministically choose a 14x14 tile outside both declared ROIs.
        safe = []
        for yy in (24, 64, 104, 144, 184, 214):
            for xx in (20, 60, 100, 140, 180, 220, 260, 296):
                candidate = (xx, yy, min(xx + 14, W - 1), min(yy + 14, H - 1))
                overlaps = lambda a, b: a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]
                if not overlaps(candidate, task) and not overlaps(candidate, critical):
                    safe.append(candidate)
        if len(safe) < 8:
            raise RuntimeError("NO_SAFE_IRRELEVANT_TILE")
        rect = safe[variant % len(safe)]
        color = f["accent"] if state else f["bg"]
    elif kind == "relevant":
        x = task[0] + 14 + (variant % 3) * 18
        y = task[1] + 27 + (variant % 2) * 14
        rect = (x, y, x + 18, y + 13)
        color = f["accent"] if state else f["bg"]
    else:
        rect = (critical[0] + 14, critical[1] + 5, critical[2] - 12, critical[3] - 5)
        color = f["panel"] if state else f["accent"]
    if kind == "irrelevant":
        c.create_rectangle(*rect, fill=color if state else f["panel"], outline=f["ink"], width=1)
    elif kind == "relevant":
        c.create_rectangle(*rect, fill=color if state else f["bg"], outline=f["ink"], width=1)
    else:
        c.create_rectangle(*rect, fill=f["panel"] if state else f["accent"], outline=f["ink"], width=1)
    return task, critical


def xget_raw(dpy, xid):
    win = dpy.create_resource_object("window", xid)
    image = win.get_image(0, 0, W, H, X.ZPixmap, 0xFFFFFFFF)
    return image.data, image.depth


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    root = tk.Tk()
    root.title("Issue 4807 fresh-family X11 fixture")
    root.geometry(f"{W}x{H}+40+40")
    root.resizable(False, False)
    root.configure(background=FAMILIES[0]["bg"])
    root.canvas = tk.Canvas(root, width=W, height=H, highlightthickness=0, bd=0)
    root.canvas.pack(fill="both", expand=True)
    wait_idle(root)
    # Capture the actual canvas child drawable: the Tk toplevel parent does not include child pixels.
    winid = int(root.canvas.winfo_id())
    dpy = display.Display()
    visual = dpy.screen().root_visual
    fmt = next(x for x in dpy.screen().allowed_depths if x.depth == root.winfo_depth()).visuals
    masks = next((v for v in fmt if v.visual_id == visual), fmt[0])
    pixmap_format = next(x for x in dpy.display.info.pixmap_formats if x.depth == root.winfo_depth())
    rows = []
    for family in range(8):
        for n in range(20):
            kind = "irrelevant" if n < 8 else ("relevant" if n < 16 else "critical")
            variant = n
            task, critical = draw(root, family, None, kind, variant, 0)
            wait_idle(root)
            before, depth = xget_raw(dpy, winid)
            draw(root, family, None, kind, variant, 1)
            wait_idle(root)
            after, depth2 = xget_raw(dpy, winid)
            if len(before) != W * H * pixmap_format.bits_per_pixel // 8 or len(after) != len(before) or depth != depth2:
                raise RuntimeError("UNEXPECTED_XIMAGE_FORMAT")
            stem = f"f{family:02d}_p{n:02d}"
            for side, data in (("before", before), ("after", after)):
                packed = zlib.compress(data, level=9)
                (OUT / f"{stem}_{side}.raw.zlib").write_bytes(packed)
                if zlib.decompress(packed) != data:
                    raise RuntimeError("LOSSLESS_ROUNDTRIP_FAILED")
            rows.append({
                "id": stem, "family": family, "split": "train" if family < 6 else "heldout",
                "kind": kind, "label_relevant": kind != "irrelevant", "critical": kind == "critical",
                "sequence": len(rows) + 1, "window_xid": winid, "width": W, "height": H,
                "depth": depth, "bits_per_pixel": pixmap_format.bits_per_pixel,
                "scanline_pad": pixmap_format.scanline_pad, "byte_order": dpy.display.info.image_byte_order,
                "red_mask": masks.red_mask, "green_mask": masks.green_mask, "blue_mask": masks.blue_mask,
                "task_roi": list(task), "critical_roi": list(critical),
                "before_sha256": digest(before), "after_sha256": digest(after),
                "before_file": f"{stem}_before.raw.zlib", "after_file": f"{stem}_after.raw.zlib",
                "raw_bytes_each": len(before),
            })
    (OUT / "pairs.jsonl").write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
    meta = {
        "schema": "issue-4807-x11-pairs-v1", "capture": "Xlib drawable.get_image X.ZPixmap from Tk/X11 window",
        "display": os.environ["DISPLAY"], "window_xid": winid, "window_geometry": [W, H],
        "pixel_format": {"depth": depth, "bits_per_pixel": pixmap_format.bits_per_pixel,
                         "scanline_pad": pixmap_format.scanline_pad,
                         "byte_order": dpy.display.info.image_byte_order,
                         "red_mask": masks.red_mask, "green_mask": masks.green_mask, "blue_mask": masks.blue_mask},
        "count": len(rows), "families": 8, "train_count": sum(r["split"] == "train" for r in rows),
        "heldout_count": sum(r["split"] == "heldout" for r in rows),
        "bundle_sha256": digest("".join(r["before_sha256"] + r["after_sha256"] for r in rows).encode()),
    }
    (OUT / "capture.json").write_text(json.dumps(meta, sort_keys=True, indent=2) + "\n")
    dpy.close()
    root.destroy()
    print(json.dumps(meta, sort_keys=True))


if __name__ == "__main__":
    main()





