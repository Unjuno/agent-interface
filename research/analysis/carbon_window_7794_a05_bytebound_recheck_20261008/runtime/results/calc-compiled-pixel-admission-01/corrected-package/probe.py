import json,sys
sys.path.insert(0,sys.argv[1])
from runtime.guarded_x11_v1.compiled import run
s=json.load(open(sys.argv[2]))
def forbidden(*args):raise RuntimeError('unexpected callback')
try:
 run(None,s,{},perceive=forbidden,verify_effect=forbidden)
except ValueError as error:
 if 'target alias' not in str(error):raise
 print(json.dumps({'status':'PASS_ARCHIVE_ALIAS_PREFLIGHT','error':str(error),'bridge_created':False,'captures':0,'callbacks':0,'inputs':0}))
else:raise RuntimeError('invalid native alias accepted')
