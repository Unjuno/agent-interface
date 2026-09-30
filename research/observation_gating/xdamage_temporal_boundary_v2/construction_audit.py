import hashlib, json, pathlib
root=pathlib.Path('/data/formal01')
cases=['QUIET','REPAINT_A','PERSIST_B','ABA_1PX','ABA_2X2','ABA_8X8']
out=[]
n=64*64*3
assert len(list(root.glob('construction_*.rgb')))==6
for c in cases:
    raw=(root/f'construction_{c}.rgb').read_bytes()
    assert len(raw)==3*n
    b,m,e=[raw[i*n:(i+1)*n] for i in range(3)]
    assert not any(b)
    if c=='PERSIST_B': assert m!=b and e!=b
    elif c.startswith('ABA_'): assert m!=b and e==b
    else: assert m==b and e==b
    out.append({'case':c,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'middle_diff':m!=b,'endpoint_diff':e!=b})
print(json.dumps({'audit':'PASS_CONSTRUCTION_BYTES','rows':out},sort_keys=True))

