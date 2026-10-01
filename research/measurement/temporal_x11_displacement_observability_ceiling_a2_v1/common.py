from __future__ import annotations
NOMINAL=7.3
BOUND=0.75
PATTERNS={
  100:[(-7.0,-7.0),(-8.0,-7.0),(7.0,7.0),(8.0,7.0)],
  200:[(-7.0,-7.0),(-7.0,-8.0),(7.0,7.0),(7.0,8.0)],
}
BOUNDARY={
  100:{'correct':188,'total':200,'unknown_phases':tuple(range(94,100)),'directions':(-1,1)},
  200:{'correct':186,'total':200,'unknown_phases':tuple(range(0,7)),'directions':(-1,1)},
}

def interval_full_compatible(d:float)->bool:
    if d>0: return abs(d-NOMINAL)<=BOUND+1e-12
    if d<0: return abs(d+NOMINAL)<=BOUND+1e-12
    return False

def pair_full_compatible(pair)->bool:
    a,b=pair
    return (a*b>0) and interval_full_compatible(a) and interval_full_compatible(b)

def blind_tail_witness(phase_ms:int)->bool:
    # If newest sample precedes query, choose a reversal halfway through the unobserved tail.
    return phase_ms>0
