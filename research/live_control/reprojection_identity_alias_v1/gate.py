"""Exact local patch gate shape copied from os_visual_followthrough_v1/controller.py.
No semantic ID or oracle input is accepted by this module.
"""
from PIL import Image
RADIUS = 5
MAX_PIXEL_ERROR = 8.0

def gate(reference_png, current_png, point):
    ref = Image.open(reference_png).convert('RGB')
    cur = Image.open(current_png).convert('RGB')
    same_shape = ref.size == cur.size
    x, y = (int(round(float(point[0]))), int(round(float(point[1]))))
    rx, ry = x, y
    r = RADIUS
    w, h = cur.size
    patch_ok = same_shape and r <= x < w-r and r <= y < h-r
    diff = None
    if patch_ok:
        rp = ref.crop((rx-r, ry-r, rx+r+1, ry+r+1))
        cp = cur.crop((x-r, y-r, x+r+1, y+r+1))
        rb = rp.tobytes(); cb = cp.tobytes()
        diff = float(max(abs(a-b) for a,b in zip(rb,cb)))
        patch_ok = diff <= MAX_PIXEL_ERROR
    return {'eligible': bool(patch_ok), 'max_pixel_error': diff, 'radius': r, 'threshold': MAX_PIXEL_ERROR}
