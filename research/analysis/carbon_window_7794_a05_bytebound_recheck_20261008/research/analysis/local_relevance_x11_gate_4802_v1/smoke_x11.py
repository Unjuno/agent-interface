"""No-write Xvfb/Tk/Python-Xlib compatibility check before freezing #4802."""
import json
import tkinter as tk

from Xlib import X, display

width, height = 320, 240
root = tk.Tk()
root.title("Issue 4802 API smoke only")
root.geometry(f"{width}x{height}+20+20")
canvas = tk.Canvas(root, width=width, height=height, highlightthickness=0)
canvas.pack(fill="both", expand=True)
canvas.create_rectangle(10, 10, 80, 80, fill="#2878a0", outline="")
root.update_idletasks()
root.update()
dpy = display.Display()
screen = dpy.screen()
depth = root.winfo_depth()
visual = screen.root_visual
depth_info = next(x for x in screen.allowed_depths if x.depth == depth)
visual_info = next(v for v in depth_info.visuals if v.visual_id == visual)
fmt = next(f for f in dpy.display.info.pixmap_formats if f.depth == depth)
xid = int(canvas.winfo_id())
image = dpy.create_resource_object("window", xid).get_image(0, 0, width, height, X.ZPixmap, 0xFFFFFFFF)
expected = width * height * fmt.bits_per_pixel // 8
if len(image.data) != expected or image.depth != depth:
    raise SystemExit("STOP_X11_CAPTURE_PREREQUISITE: canvas XGetImage geometry/format mismatch")
print(json.dumps({"decision": "PASS_X11_API_SMOKE", "window_xid": xid, "geometry": [width, height],
                  "depth": depth, "visual_id": visual_info.visual_id, "bits_per_pixel": fmt.bits_per_pixel,
                  "scanline_pad": fmt.scanline_pad, "image_byte_order": dpy.display.info.image_byte_order,
                  "xgetimage_bytes": len(image.data), "dataset_written": False, "model_called": False}, sort_keys=True))
dpy.close()
root.destroy()

