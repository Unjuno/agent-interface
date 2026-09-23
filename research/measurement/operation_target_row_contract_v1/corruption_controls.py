from contract import validate_row,validate_dataset
from generator import base,mutate
import random
rng=random.Random(77);cs=[]
def reject(name,r):
 try:validate_row(r);ok=False
 except ValueError:ok=True
 cs.append({'name':name,'rejected':ok})
for k,n in enumerate(['future_leakage','stale_target_epoch','unsupported_operation','invented_text','missing_identity','duplicate_target','incompatible_proposal','done_without_verifier','authority_promotion','nonindependent_oracle']):reject(n,mutate(base(700+k,rng),k))
a=base(900,rng);b=base(901,rng);b['episode_id']=a['episode_id'];b['split']='eval' if a['split']=='train' else 'train'
try:validate_dataset([a,b]);ok=False
except ValueError:ok=True
cs.append({'name':'episode_split_leakage','rejected':ok});assert all(x['rejected'] for x in cs);print('CORRUPTION_PASS',len(cs))
