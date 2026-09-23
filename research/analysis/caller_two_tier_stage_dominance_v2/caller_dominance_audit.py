import ast,hashlib,json,sys
path=sys.argv[1]; src=open(path,'rb').read(); tree=ast.parse(src,filename=path)
run=next((n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run'),None)
if run is None: raise SystemExit('HOLD_MISSING_RUN')
calls=[]
class V(ast.NodeVisitor):
 def visit_Call(self,n):
  if isinstance(n.func,ast.Name) and n.func.id=='local' and n.args and isinstance(n.args[0],ast.Constant): calls.append((n.args[0].value,n.lineno))
  self.generic_visit(n)
V().visit(run)
final=[x for x in calls if x[0]=='final_revalidate']; exe=[x for x in calls if x[0]=='execute']
nested=[]
for n in ast.walk(run):
 if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n is not run:
  for c in ast.walk(n):
   if isinstance(c,ast.Call) and isinstance(c.func,ast.Name) and c.func.id=='local' and c.args and isinstance(c.args[0],ast.Constant) and c.args[0].value=='execute': nested.append(c.lineno)
errors=[]
if len(final)!=1: errors.append('expected exactly one final_revalidate call')
if len(exe)!=1: errors.append('expected exactly one execute call')
if nested: errors.append('nested execute call sites '+str(nested))
if final and exe and not final[0][1] < exe[0][1]: errors.append('execute not after final_revalidate')
out={'source_sha256':hashlib.sha256(src).hexdigest(),'run_lines':[run.lineno,run.end_lineno],'calls':calls,'final_revalidate':final,'execute':exe,'nested_execute':nested,'decision':'PASS_CALLER_TWO_TIER_STAGE_DOMINANCE_SCOPED' if not errors else 'FAIL_EXECUTE_OUTSIDE_FINAL_GATE','errors':errors}
print(json.dumps(out,sort_keys=True))
sys.exit(bool(errors))
