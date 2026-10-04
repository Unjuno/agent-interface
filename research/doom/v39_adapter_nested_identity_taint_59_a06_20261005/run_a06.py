"""Replay all adapter cardinality regressions against frozen A05 and candidate."""
from __future__ import annotations
import ast,contextlib,hashlib,io,json
from pathlib import Path
import unittest
from types import SimpleNamespace
ROOT=Path("/src"); DOOM=ROOT/"research/doom"; HERE=DOOM/"v39_adapter_nested_identity_taint_59_a06_20261005"
BASELINE=HERE/"BASELINE_SOURCE.py"; TESTS=DOOM/"test_map01_v39_typed_state_feedback.py"; RAW=DOOM/"map01_v39_perkey_bridge_a01/results/construction-a01/candidate-events.jsonl"; OUTPUT=Path("/out/A06_RESULT.json")
METHODS=("test_input_edge_receipt_rejects_duplicate_adapter_rows","test_input_edge_receipt_rejects_unknown_outer_event_with_adapter_edge","test_input_edge_receipt_rejects_legacy_transition_with_adapter_edge","test_input_edge_receipt_rejects_outer_nested_token_conflict")
SUBCASES=["duplicate_down_identical","duplicate_up_identical","duplicate_both_identical","duplicate_down_conflicting","duplicate_up_conflicting","duplicate_down_unknown_kind","duplicate_up_unknown_kind","down_unknown_kind","up_unknown_kind","duplicate_up_as_legacy_transition","only_legacy_transition_up","duplicate_down_outer_token_changed","duplicate_up_outer_token_changed"]
def load_function(path,name,globals_):
 tree=ast.parse(path.read_text(encoding="utf-8")); node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name); module=ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])); exec(compile(module,str(path),"exec"),globals_); return globals_[name]
def run(source):
 projector=load_function(source,"input_edge_receipts",{"hashlib":hashlib}); tree=ast.parse(TESTS.read_text(encoding="utf-8")); original=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=="V39TypedStateFeedbackTests"); methods=[next(n for n in original.body if isinstance(n,ast.FunctionDef) and n.name==name) for name in METHODS]
 cls=ast.ClassDef(name="A06AdapterIdentityTests",bases=[ast.Attribute(value=ast.Name(id="unittest",ctx=ast.Load()),attr="TestCase",ctx=ast.Load())],keywords=[],body=methods,decorator_list=[]); module=ast.Module(body=[ast.Import(names=[ast.alias(name="json")]),ast.Import(names=[ast.alias(name="unittest")]),cls],type_ignores=[]); env={"HERE":DOOM,"controller":SimpleNamespace(input_edge_receipts=projector)}; exec(compile(ast.fix_missing_locations(module),str(TESTS),"exec"),env); suite=unittest.defaultTestLoader.loadTestsFromTestCase(env["A06AdapterIdentityTests"]); stream=io.StringIO()
 with contextlib.redirect_stderr(stream),contextlib.redirect_stdout(stream): result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
 return result.wasSuccessful(),stream.getvalue(),result.testsRun,len(result.failures)+len(result.errors)
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
bok,blog,btests,bbad=run(BASELINE); cok,clog,ctests,cbad=run(DOOM/"map01_overlap_controller_v39.py")
for path in (DOOM/"map01_overlap_controller_v39.py",TESTS): compile(path.read_text(encoding="utf-8"),str(path),"exec")
record={"experiment":"V39_ADAPTER_NESTED_IDENTITY_TAINT_A06","baseline_commit":"a3155bec0b21d29557dbd4bd3d7218eb039cb135","baseline_source_sha256":digest(BASELINE),"candidate_source_sha256":digest(DOOM/"map01_overlap_controller_v39.py"),"test_sha256":digest(TESTS),"fixture_sha256":digest(RAW),"methods":list(METHODS),"baseline":{"expected_fail":not bok,"tests":btests,"failed_tests":bbad,"output":blog},"candidate":{"passed":cok,"tests":ctests,"failed_tests":cbad,"output":clog},"syntax_compile":"PASS","subcases":SUBCASES}
OUTPUT.write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8"); print(json.dumps({k:v for k,v in record.items() if k not in ("baseline","candidate")},indent=2)); print("BASELINE\n"+blog); print("CANDIDATE\n"+clog); raise SystemExit(0 if (not bok and cok) else 1)
