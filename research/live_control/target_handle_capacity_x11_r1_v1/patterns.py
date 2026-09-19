SIZE=16

def rgb_for(label,x,y):
    if label=='A':
        return ((31*x+17*y+43)%256,(7*x+29*y+101)%256,(19*x+11*y+151)%256)
    if label=='B':
        return ((13*x+23*y+197)%256,(37*x+5*y+61)%256,(3*x+41*y+17)%256)
    raise ValueError(label)

def template_bytes(label):
    out=bytearray()
    for y in range(SIZE):
        for x in range(SIZE):
            out.extend(rgb_for(label,x,y))
    return bytes(out)
