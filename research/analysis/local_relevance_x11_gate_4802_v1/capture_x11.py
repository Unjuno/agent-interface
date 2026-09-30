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
    {"bg": "#f4f1ea", "panel": "#ffffff", "ink": "#242424", "accent": "#2878a0", "shift": False},
    {"bg": "#eceff2", "panel": "#ffffff", "ink": "#202830", "accent": "#b34f36", "shift": False},
    {"bg": "#f5f0e5", "panel": "#fffdf8", "ink": "#342d25", "accent": "#56804c", "shift": False},
    {"bg": "#e9eef4", "panel": "#fbfdff", "ink": "#20283c", "accent": "#7053a1", "shift": False},
    {"bg": "#132235", "panel": "#263c55", "ink": "#f0f4f8", "accent": "#f0b64b", "shift": True},
    {"bg": "#f8e7ee", "panel": "#fff8fb", "ink": "#431f35", "accent": "#c02d72", "shift": True},
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
    if family in (0, 1, 2, 3):
        box = (20, 20, 300, 220)
        task = (42 + (family % 2) * 6, 76 + (family % 2) * 4, 164 + (family % 2) * 6, 146 + (family % 2) * 4)
        critical = (174, 164, 270, 202)
    elif family == 4:
        box, task, critical = (12, 16, 308, 224), (50, 82, 185, 156), (195, 168, 286, 211)
    else:
        box, task, critical = (28, 12, 292, 228), (135, 44, 270, 117), (40, 168, 130, 211)
    # Draw a source window with a family-specific geometry and stable task/critical regions.
    c.create_rectangle(*box, fill=f["panel"], outline=f["accent"], width=3)
    c.create_text(box[0] + 16, box[1] + 14, anchor="nw", text=f"Workspace family {family}", fill=f["ink"], font=("TkDefaultFont", 10, "bold"))
    c.create_rectangle(*task, fill=f["bg"], outline=f["ink"], width=2)
    c.create_text(task[0] + 6, task[1] + 4, anchor="nw", text="TASK VALUE", fill=f["ink"], font=("TkDefaultFont", 9))
    c.create_rectangle(*critical, fill=f["accent"], outline=f["ink"], width=1)
    c.create_text((critical[0] + critical[2]) // 2, (critical[1] + critical[3]) // 2, text="LOCK", fill=f["panel"], font=("TkDefaultFont", 8, "bold"))
    # The changed tile is either outside task/critical, inside task, or in critical ROI.
    if kind == "irrelevant":
        x, y = 220 + (variant % 3) * 10, 60 + (variant % 2) * 22
        if family == 5:
            x, y = 45 + (variant % 3) * 10, 60 + (variant % 2) * 22
        rect = (x, y, x + 13 + (variant % 4), y + 12 + (variant % 3))
        color = f["accent"] if state else f["bg"]
        # Keep the irrelevant change disjoint from task & critical masks by placing top-right/bottom-left.
        if family == 4:
            rect = (220 + (variant % 2) * 9, 52 + (variant % 3) * 10, 238 + (variant % 2) * 9, 67 + (variant % 3) * 10)
        if family == 5:
            rect = (46 + (variant % 2) * 10, 55 + (variant % 3) * 10, 63 + (variant % 2) * 10, 70 + (variant % 3) * 10)
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
    root.title("Issue 4799 fixed X11 fixture")
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
    for family in range(6):
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
                "id": stem, "family": family, "split": "train" if family < 4 else "heldout",
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
        "schema": "issue-4799-x11-pairs-v1", "capture": "Xlib drawable.get_image X.ZPixmap from Tk/X11 window",
        "display": os.environ["DISPLAY"], "window_xid": winid, "window_geometry": [W, H],
        "pixel_format": {"depth": depth, "bits_per_pixel": pixmap_format.bits_per_pixel,
                         "scanline_pad": pixmap_format.scanline_pad,
                         "byte_order": dpy.display.info.image_byte_order,
                         "red_mask": masks.red_mask, "green_mask": masks.green_mask, "blue_mask": masks.blue_mask},
        "count": len(rows), "families": 6, "train_count": sum(r["split"] == "train" for r in rows),
        "heldout_count": sum(r["split"] == "heldout" for r in rows),
        "bundle_sha256": digest("".join(r["before_sha256"] + r["after_sha256"] for r in rows).encode()),
    }
    (OUT / "capture.json").write_text(json.dumps(meta, sort_keys=True, indent=2) + "\n")
    dpy.close()
    root.destroy()
    print(json.dumps(meta, sort_keys=True))


if __name__ == "__main__":
    main()



