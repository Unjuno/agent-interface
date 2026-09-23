import random
from model import Event
SEED=104320260918004
LIFETIMES=250000
CHUNKS=25
PER_CHUNK=10000
OWNERS=('ownerA','ownerB','ownerC')
INTENTS=('move','cover','interact')
KEYS=('F8','F9','LEFT','RIGHT')
OPS=('down','down','down','up','up','cleanup')
def sequence(index):
    rng=random.Random((SEED ^ (index*0x9E3779B97F4A7C15)) & ((1<<64)-1))
    n=rng.randrange(1,21); out=[]
    for _ in range(n):
        out.append(Event(rng.choice(OPS),rng.choice(OWNERS),rng.choice(INTENTS),rng.choice(KEYS),rng.random()<0.62))
    return out
