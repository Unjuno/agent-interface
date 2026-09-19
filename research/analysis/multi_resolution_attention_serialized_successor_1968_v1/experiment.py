import hashlib, json

W, H = 64, 40
REGIONS = {
    'toolbar': (2, 2, 20, 5, 40),
    'dialog': (16, 12, 32, 16, 90),
    'tiny_status': (52, 4, 8, 3, 210),
    # visually identical labels; context/position must disambiguate them
    'label_left': (4, 30, 10, 4, 137),
    'label_right': (46, 30, 10, 4, 137),
}

def frame(changes=()):
    p = bytearray([17] * (W * H))
    for x, y, w, h, v in REGIONS.values():
        for yy in range(y, y+h):
            for xx in range(x, x+w): p[yy*W+xx] = v
    for name, value in changes:
        x, y, w, h, _ = REGIONS[name]
        for yy in range(y, y+h):
            for xx in range(x, x+w): p[yy*W+xx] = value
    return bytes(p)

def enc(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()

def digest(b): return hashlib.sha256(b).hexdigest()

def low(data):
    return bytes(data[y*4*W+x*4] for y in range(H//4) for x in range(W//4))

def crop(data, r):
    x, y, w, h, _ = r
    return bytes(data[yy*W+xx] for yy in range(y,y+h) for xx in range(x,x+w))

def package(data, changed, mode):
    if mode == 'FULL':
        return {'version':1, 'mode':'FULL', 'width':W, 'height':H, 'pixels':data.hex()}
    patches=[]
    for name, value in changed:
        r=REGIONS[name]
        patches.append({'context':'left' if name=='label_left' else 'right' if name=='label_right' else name,
                        'name':name, 'rect':r[:4], 'value':value,
                        'pixels':crop(data,r).hex()})
    return {'version':1, 'mode':mode, 'width':W, 'height':H,
            'base_recipe':'fixture-v2', 'global_low':low(data).hex(), 'patches':patches}

def reconstruct(pkg):
    if pkg['mode']=='FULL': return bytes.fromhex(pkg['pixels'])
    p=bytearray(frame())
    for patch in pkg['patches']:
        x,y,w,h=patch['rect']; vals=bytes.fromhex(patch['pixels']); i=0
        for yy in range(y,y+h):
            for xx in range(x,x+w): p[yy*W+xx]=vals[i]; i+=1
    return bytes(p)

def main():
    cases=[(), (('tiny_status',233),), (('dialog',117),),
           (('label_left',155),), (('label_right',155),),
           (('label_left',155),('label_right',155)), (('toolbar',77),)]
    rows=[]
    for changed in cases:
        source=frame(changed)
        for mode in ('FULL','GLOBAL_LOW_PLUS_PATCHES'):
            pkg=package(source,changed,mode); raw=enc(pkg); rebuilt=reconstruct(pkg)
            rows.append({'changed':changed,'mode':mode,'exact':rebuilt==source,
                         'bytes':len(raw),'sha':digest(raw)})
    for mode in ('FULL','GLOBAL_LOW_PLUS_PATCHES'):
        xs=[r for r in rows if r['mode']==mode]
        print(mode,'exact',sum(r['exact'] for r in xs),'/',len(xs),'bytes',sorted(set(r['bytes'] for r in xs)))
    print('rows',len(rows),'manifest_sha',digest(enc(REGIONS)))
    assert all(r['exact'] for r in rows)
    assert min(r['bytes'] for r in rows if r['mode']=='GLOBAL_LOW_PLUS_PATCHES') < min(r['bytes'] for r in rows if r['mode']=='FULL')

if __name__=='__main__': main()

