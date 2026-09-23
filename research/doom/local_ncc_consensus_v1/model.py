"""Research-only horizontal correspondence estimators for Issue #4163."""
from __future__ import annotations
import numpy as np

SEARCH_LIMIT = 240
MIN_CORR = 0.20
MIN_MARGIN = 0.02
BANDS = 5
CONSENSUS_TOLERANCE = 2
MIN_CONSENSUS = 3
STOP_GATE_PX = 34

def _gradient(a: np.ndarray) -> np.ndarray:
    if a.ndim != 2 or a.shape != (140, 320):
        raise ValueError("expected 140x320 grayscale array")
    return np.diff(a.astype(np.float64), axis=1)

def _ncc(ref: np.ndarray, cur: np.ndarray, shift: int):
    if shift >= 0:
        a = ref[:, : ref.shape[1] - shift] if shift else ref
        b = cur[:, shift:] if shift else cur
    else:
        a = ref[:, -shift:]
        b = cur[:, : cur.shape[1] + shift]
    if a.size < 100:
        return None
    av = a.ravel().astype(np.float64); bv = b.ravel().astype(np.float64)
    av -= av.mean(); bv -= bv.mean()
    da = np.linalg.norm(av); db = np.linalg.norm(bv)
    if da < 1e-12 or db < 1e-12:
        return None
    return float(av @ bv / (da * db))

def estimate_global(ref: np.ndarray, cur: np.ndarray) -> dict:
    rg, cg = _gradient(ref), _gradient(cur)
    vals=[]
    for s in range(-SEARCH_LIMIT, SEARCH_LIMIT + 1):
        v=_ncc(rg,cg,s)
        if v is not None: vals.append((v,s))
    if len(vals) < 2:
        return {"status":"UNKNOWN_FLAT","shift_px":None,"best_ncc":None,"margin":None,"goal":None}
    vals.sort(reverse=True)
    best,s=vals[0]; margin=best-vals[1][0]
    if best < MIN_CORR or margin < MIN_MARGIN:
        return {"status":"UNKNOWN_AMBIGUOUS","shift_px":None,"best_ncc":best,"margin":margin,"goal":None}
    return {"status":"IDENTIFIED","shift_px":int(s),"best_ncc":best,"margin":margin,"goal":abs(s)<=STOP_GATE_PX}

def estimate_band_consensus(ref: np.ndarray, cur: np.ndarray) -> dict:
    if ref.shape != (140,320) or cur.shape != (140,320):
        raise ValueError("expected 140x320 grayscale arrays")
    height=ref.shape[0]//BANDS
    bands=[]
    shifts=[]
    for i in range(BANDS):
        r=ref[i*height:(i+1)*height]
        c=cur[i*height:(i+1)*height]
        d=estimate_global(np.repeat(r, BANDS, axis=0)[:140], np.repeat(c, BANDS, axis=0)[:140])
        bands.append(d)
        if d["status"] == "IDENTIFIED": shifts.append(d["shift_px"])
    best_cluster=[]
    for s in shifts:
        cluster=[x for x in shifts if abs(x-s)<=CONSENSUS_TOLERANCE]
        if len(cluster)>len(best_cluster): best_cluster=cluster
    if len(best_cluster) < MIN_CONSENSUS:
        return {"status":"UNKNOWN_NO_CONSENSUS","shift_px":None,"goal":None,"bands":bands,"support":len(best_cluster)}
    shift=int(round(float(np.median(best_cluster))))
    return {"status":"IDENTIFIED","shift_px":shift,"goal":abs(shift)<=STOP_GATE_PX,"bands":bands,"support":len(best_cluster)}
