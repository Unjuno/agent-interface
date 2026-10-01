from fractions import Fraction

def validate(W,U,dW,dU,a,b):
    vals=(W,U,dW,dU,a,b)
    if not all(isinstance(x,int) for x in vals): raise ValueError('integers required')
    if W<0 or U<0 or W>U: raise ValueError('base interval')
    if dW<0 or dW>W or dU<0 or dU>U: raise ValueError('refinement')
    if not (0<a<b): raise ValueError('q')
    W2=W-dW; U2=U-dU
    if U2<=0: raise ValueError('zero refined upper')
    if W2>U2: raise ValueError('refined interval')
    return W2,U2

def frontier_pass(W,U,dW,dU,a,b):
    validate(W,U,dW,dU,a,b)
    return b*dW-a*dU >= b*W-a*U

def direct_pass(W,U,dW,dU,a,b):
    W2,U2=validate(W,U,dW,dU,a,b)
    return Fraction(W2,U2) <= Fraction(a,b)

def deficit(W,U,a,b):
    if W<0 or U<0 or W>U or not (0<a<b): raise ValueError
    return b*W-a*U

def min_pure_width(W,U,a,b):
    D=deficit(W,U,a,b)
    return 0 if D<=0 else (D+b-1)//b

def min_lower_fixed_upper_inward(W,U,a,b):
    # lower fixed => shrinking upper by x also shrinks width by x: dW=dU=x
    D=deficit(W,U,a,b)
    den=b-a
    return 0 if D<=0 else (D+den-1)//den
