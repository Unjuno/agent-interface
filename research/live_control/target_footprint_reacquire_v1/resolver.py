"""Bounded visual footprint retrieval; outputs evidence, never input authority.

RGB uint8 inputs, fixed-scale translation only. No document/model/engine access.
A full appearance match is not semantic identity. Duplicate appearances refuse.
"""
from __future__ import annotations
import math
import cv2
import numpy as np

SEARCH_RADIUS = 120
MAX_RMSE = 20.0
AMBIGUITY_SLACK = 3.0
MAX_AGE_NS = 500_000_000


def resolve(image: np.ndarray, template: np.ndarray, prediction: list[float]) -> dict:
    if image.dtype != np.uint8 or template.dtype != np.uint8:
        raise ValueError('RGB uint8 required')
    if image.ndim != 3 or template.ndim != 3 or image.shape[2] != 3 or template.shape[2] != 3:
        raise ValueError('three-channel images required')
    th, tw = template.shape[:2]
    if min(th, tw) < 15 or max(th, tw) > 81:
        raise ValueError('footprint dimensions outside frozen scope')
    if not np.isfinite(prediction).all():
        raise ValueError('nonfinite projection')
    h, w = image.shape[:2]
    px, py = map(float, prediction)
    rx, ry = tw // 2, th // 2
    left = max(rx, math.ceil(px - SEARCH_RADIUS))
    right = min(w - tw + rx, math.floor(px + SEARCH_RADIUS))
    top = max(ry, math.ceil(py - SEARCH_RADIUS))
    bottom = min(h - th + ry, math.floor(py + SEARCH_RADIUS))
    if right < left or bottom < top:
        return {'status': 'OUT_OF_BOUNDS', 'eligible': False}
    crop = image[top-ry:bottom-ry+th, left-rx:right-rx+tw]
    raw = cv2.matchTemplate(crop, template, cv2.TM_SQDIFF)
    rmse = np.sqrt(np.maximum(raw.astype(np.float64), 0.0) / template.size)
    _, _, best, _ = cv2.minMaxLoc(rmse)
    bx, by = best
    value = float(rmse[by, bx])
    # Spatially distinct alternative; nearby shifts of one object are not duplicates.
    distinct = rmse.copy()
    suppression = max(8, min(th, tw) // 2)
    distinct[max(0,by-suppression):by+suppression+1, max(0,bx-suppression):bx+suppression+1] = np.inf
    second = float(np.min(distinct))
    status = 'MISSING' if value > MAX_RMSE else ('AMBIGUOUS' if second <= MAX_RMSE + AMBIGUITY_SLACK else 'UNIQUE')
    return dict(status=status, eligible=status=='UNIQUE', point=[left+bx,top+by],
                best_rmse=value, second_rmse=second if math.isfinite(second) else None,
                search_box=[left-rx,top-ry,right-left+tw,bottom-top+th],
                candidate_positions=int(rmse.size), template_shape=[th,tw],
                radius_px=SEARCH_RADIUS, max_rmse=MAX_RMSE)


def center_gate(reference: np.ndarray, image: np.ndarray, source_point, prediction) -> dict:
    x,y = [int(round(float(v))) for v in prediction]
    sx,sy = [int(round(float(v))) for v in source_point]
    r=5; h,w=image.shape[:2]
    if not(r<=x<w-r and r<=y<h-r):
        return dict(status='OUT_OF_BOUNDS',eligible=False,point=[x,y])
    delta=float(np.max(np.abs(reference[sy-r:sy+r+1,sx-r:sx+r+1].astype(float)-image[y-r:y+r+1,x-r:x+r+1].astype(float))))
    return dict(status='MATCH' if delta<=8 else 'MISSING',eligible=delta<=8,point=[x,y],max_pixel_error=delta)
