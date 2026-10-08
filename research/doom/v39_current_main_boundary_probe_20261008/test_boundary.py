import ast, json, pathlib, sys, unittest
path=pathlib.Path(sys.argv[-1]); src=path.read_text(encoding='utf-8-sig'); tree=ast.parse(src)
node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='cancel_invalidated_cover')
ns={'json':json,'RuntimeError':RuntimeError}; exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),ns); fn=ns['cancel_invalidated_cover']
class Planner:
 def __init__(self): self.calls=[]
 def interrupt(self,h): self.calls.append(h); return {'status':'interrupted'}
class Pipe:
 def __init__(self): self.writes=[]
 def write(self,x): self.writes.append(x)
 def flush(self): pass
class Proc:
 def __init__(self): self.stdin=Pipe()
class Boundary(unittest.TestCase):
 def call(self,status,release):
  p=Planner(); proc=Proc(); term={'event':'terminal','id':'cover-1','status':status,'release':release}
  result=fn(p,'planner-1',proc,lambda pred:term,'cover-1')
  self.assertEqual(p.calls,['planner-1']); self.assertEqual(json.loads(proc.stdin.writes[0]),{'op':'cancel','id':'cover-1'}); self.assertIs(result[1],term)
 def test_cancelled_empty_release(self): self.call('cancelled',{'verified':True,'keys_down':[],'buttons_down':[]})
 def test_race_completed_or_expired_empty_release(self):
  for state in ('completed','expired'):
   with self.subTest(state=state): self.call(state,{'verified':True,'keys_down':[],'buttons_down':[]})
 def test_held_unverified_failed_and_missing_release_rejected(self):
  cases=[('completed',{'verified':True,'keys_down':['space'],'buttons_down':[]}),('expired',{'verified':False,'keys_down':[],'buttons_down':[]}),('failed',{'verified':True,'keys_down':[],'buttons_down':[]}),('needs_decision',{'verified':True,'keys_down':[],'buttons_down':[]}),('completed',{})]
  for state,release in cases:
   with self.subTest(state=state,release=release), self.assertRaisesRegex(RuntimeError,'invalidated cover did not verify empty release'): self.call(state,release)
if __name__=='__main__': unittest.main(argv=['boundary'],verbosity=2)
