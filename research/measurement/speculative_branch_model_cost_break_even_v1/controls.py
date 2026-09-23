import copy,json
from pathlib import Path
from audit import verify
HERE=Path(__file__).parent
# Toy-only construction; do not load retained parent values here.
toy={'k2':{'temporal_mean_ms':10.0},'k1':{'temporal_mean_ms':20.0},'local_marginal_ns':{'mean':1_000_000,'p50':2_000_000,'p95':3_000_000,'p99':4_000_000}}
raw=toy['k1']['temporal_mean_ms']-toy['k2']['temporal_mean_ms']; assert raw==10.0
assert {k:raw-v/1e6 for k,v in toy['local_marginal_ns'].items()}=={'mean':9.0,'p50':8.0,'p95':7.0,'p99':6.0}
print('TOY_FORMULA_PASS')
