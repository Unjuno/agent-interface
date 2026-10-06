"""Conservative two-frame TTC interval for bounded radius error."""
from math import isfinite

def interval_ttc(r1,t1,r2,t2,error_bound):
 vals=(r1,t1,r2,t2,error_bound)
 if not all(isfinite(x) for x in vals) or error_bound<0 or t2<=t1: return None
 lo1,hi1=r1-error_bound,r1+error_bound
 lo2,hi2=r2-error_bound,r2+error_bound
 if lo1<=0 or lo2<=0 or lo2<=hi1: return None
 dt=t2-t1
 corners=(lo2*dt/(lo2-lo1),lo2*dt/(lo2-hi1),hi2*dt/(hi2-lo1),hi2*dt/(hi2-hi1))
 if not all(isfinite(x) and x>0 for x in corners): return None
 return min(corners),max(corners)

def classify(interval,threshold=2.0):
 if interval is None or not isfinite(threshold) or threshold<=0: return "UNKNOWN"
 lo,hi=interval
 if not (isfinite(lo) and isfinite(hi) and 0<lo<=hi): return "UNKNOWN"
 if hi<=threshold: return "YIELD"
 if lo>threshold: return "CLEAR"
 return "UNKNOWN"
