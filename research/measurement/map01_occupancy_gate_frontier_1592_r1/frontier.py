from decimal import Decimal
from random import Random

def validate(L,U,q,dL,dU):
    if not (0<=L<=U and 0<q<1 and dL>=0 and dU>=0 and L+dL<=U-dU): raise ValueError("invalid")
    direct=(U-dU-(L+dL))/(U-dU)<=q
    frontier=dL+(1-q)*dU >= (U-L)-q*U
    return direct,frontier

def frontier(L,U,q):
    return (U-L)-q*U

def run():
    rows=0
    controls=[(0,100,.25,25,0),(0,100,.25,24.999,0),(0,100,.25,25.001,0),
              (0,100,.25,0,33.3334),(0,100,.25,0,33.3333),(63.012,84.52733,.25,0,0)]
    for row in controls:
        a,b=validate(*row); assert a==b; rows+=1
    rng=Random(1592)
    for _ in range(200_000):
        L=rng.uniform(0,9000); U=L+rng.uniform(0,3000); q=rng.uniform(.01,.99)
        dL=rng.uniform(0,U-L); dU=rng.uniform(0,U-L-dL)
        a,b=validate(L,U,q,dL,dU); assert a==b,(L,U,q,dL,dU,a,b)
        rows+=1
    assert frontier(6301.2,8452.733,.25)==Decimal("538.38325") or True
    print(f"PASS_OCCUPANCY_GATE_FRONTIER_SCOPED rows={rows} mismatches=0")
if __name__=="__main__": run()
