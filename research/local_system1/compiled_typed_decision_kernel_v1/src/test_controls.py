import numpy as np
from kernel import CompiledTypedDecisionKernel, HEADS, INPUT_DIM, validate_typed_output
k=CompiledTypedDecisionKernel(8192,876)
x=np.linspace(-1,1,INPUT_DIM,dtype=np.float32)
r=k.decide(x)
assert k.w1.size+k.w2.size+k.tail.size==8192
assert k.parameter_bytes==8192*4
assert len(r['outputs'])==len(HEADS)==33
assert validate_typed_output(r)==[]
assert r['yield_count']>0
assert all(o['selected']=='YIELD' or isinstance(o['selected'],str) for o in r['outputs'])
print('tiny mechanics PASS',r['yield_count'],k.hidden_dim,k.tail_count)
