import ast,sys,types,unittest,os,importlib.util,json
from pathlib import Path
src=Path('/source');out=Path('/out')
proxy_tree=ast.parse((src/'session14.py').read_bytes())
proxy=next(n for n in proxy_tree.body if isinstance(n,ast.ClassDef)and n.name=='_GameProxy')
context={'sys':sys};exec(compile(ast.Module(body=[proxy],type_ignores=[]),'session14-class','exec'),context)
candidate=types.SimpleNamespace(_GameProxy=context['_GameProxy'])
test_tree=ast.parse((src/'test_session15.py').read_bytes())
fixture=next(n for n in test_tree.body if isinstance(n,ast.ClassDef)and n.name=='GameProxyLifecycleTests')
context={'unittest':unittest,'candidate':candidate};exec(compile(ast.Module(body=[fixture],type_ignores=[]),'unchanged-proxy-fixture','exec'),context)
os.environ['OWNER_UNDER_TEST']=str(src/'owner12.py')
spec=importlib.util.spec_from_file_location('cause_fixture',src/'cause_test.py');cause=importlib.util.module_from_spec(spec);spec.loader.exec_module(cause)
suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(context['GameProxyLifecycleTests']),unittest.defaultTestLoader.loadTestsFromTestCase(cause.CancellationReleaseCauseTests)])
result=unittest.TextTestRunner(verbosity=2).run(suite)
record={'tests':result.testsRun,'errors':len(result.errors),'failures':len(result.failures),'success':result.wasSuccessful(),'scope':'Seven unchanged V15 fake proxy lifecycle cases retargeted to exact V14 class AST, three unchanged cause fixtures target richer owner12 with fake Xlib/real thread. Not full session/native engine/formal allocation.'}
(out/'RESULT.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
raise SystemExit(0 if result.wasSuccessful()else 1)
