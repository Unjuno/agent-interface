from contract import validate_row,validate_dataset
from oracle import row_valid,dataset_valid
from generator import base,mutate
import random
rng=random.Random(1)
for i in range(8):
 r=base(i,rng); assert row_valid(r); validate_row(r)
for k in range(10):
 r=mutate(base(100+k,rng),k); assert not row_valid(r)
 try: validate_row(r); raise AssertionError(k)
 except ValueError: pass
a=base(300,rng);b=base(301,rng);b['episode_id']=a['episode_id'];b['split']='eval' if a['split']=='train' else 'train'
assert not dataset_valid([a,b])
try:validate_dataset([a,b]);raise AssertionError('split')
except ValueError:pass
print('MECHANICS_PASS')
