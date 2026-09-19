from __future__ import annotations
from common_parent import *
ACCEL_ARMS={"AM2":-20_000,"AM1":-10_000,"A0":0,"AP1":10_000,"AP2":20_000}
ASSUMED_BOUND_U=1000
def _round_div(n:int,d:int)->int:
    if n>=0:return (n+d//2)//d
    return -((-n+d//2)//d)
def position_accel_u(t_us:int,reversal_age_ms:int,post_dir:int,accel_ppm_per_period:int)->int:
    r_us=-reversal_age_ms*1000; pre_dir=-post_dir
    if t_us<=r_us:return pre_dir*(t_us-r_us)
    dt=t_us-r_us
    extra=_round_div(accel_ppm_per_period*dt*dt,2*PERIOD_US*1_000_000)
    return post_dir*(dt+extra)
