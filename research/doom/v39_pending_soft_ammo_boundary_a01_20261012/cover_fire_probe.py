from __future__ import annotations
import ast, hashlib, json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
source=ROOT/'source/map01_overlap_controller_v39.py'
schema_path=ROOT/'source/map01_cover_policy_schema_v6.json'
tree=ast.parse(source.read_text(encoding='utf-8'))
funcs={node.name:node for node in tree.body if isinstance(node,ast.FunctionDef)}
ns={}
exec(compile(ast.Module(body=[funcs['compile_commands'],funcs['compile_cover']],type_ignores=[]),str(source),'exec'),ns)
command=[{'action':'fire','extent':'pulse'}]
steps=ns['compile_cover'](command)
fire_holds=[row for row in steps if row.get('op')=='hold' and row.get('keys')==['space']]
main=funcs['main']
def pending_loop(node):
    if not isinstance(node,ast.While): return False
    test=node.test
    return (isinstance(test,ast.UnaryOp) and isinstance(test.op,ast.Not)
            and isinstance(test.operand,ast.Call) and isinstance(test.operand.func,ast.Attribute)
            and test.operand.func.attr=='done' and isinstance(test.operand.func.value,ast.Name)
            and test.operand.func.value.id=='future')
loops=[n for n in ast.walk(main) if pending_loop(n)]
renewal=any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='submit_cover'
            for loop in loops for n in ast.walk(loop))
schema=json.loads(schema_path.read_text(encoding='utf-8'))
cover_schema=schema['properties']['next_cover']
cover_validity=schema['properties']['next_cover_validity']['items']['properties']
action_validity=schema['properties']['action_validity']['items']['properties']
raw=json.loads((ROOT/'results/raw.json').read_text(encoding='utf-8'))
soft=raw['cases'][0]
checks=[]
def ck(name,condition):
    checks.append({'name':name,'pass':bool(condition)})
    if not condition: raise RuntimeError('failed: '+name)
ck('schema_allows_fire_in_next_cover', 'fire' in cover_schema['items']['properties']['action']['enum'])
ck('cover_validity_has_no_ammo_floor', 'minimum_ammo' not in cover_validity)
ck('next_action_has_ammo_floor', 'minimum_ammo' in action_validity)
ck('fire_pulse_compiles_eight_repetitions', len(fire_holds)==8)
ck('bounded_cover_sums_to_ten_seconds', sum(row['duration_ms'] for row in steps)==10000)
ck('cover_fire_dwell_is_eight_hundred_ms', sum(row['duration_ms'] for row in fire_holds)==800)
ck('pending_planner_loop_contains_cover_renewal', bool(loops) and renewal)
ck('soft_ammo_case_does_not_cancel', soft['current_ammo']==4 and soft['monitor_result'] is None and not soft['pending_turn_cancel_signal'])
result={'schema':'issue59-pending-soft-cover-fire-a02','source_commit':'f185a9059d485a4f8d5a65e9e7f6782897f67eae','controller_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'schema_sha256':hashlib.sha256(schema_path.read_bytes()).hexdigest(),'cover_program':steps,'fire_hold_count':len(fire_holds),'fire_hold_total_ms':sum(row['duration_ms'] for row in fire_holds),'soft_case':soft,'pending_loop_renewal_call':renewal,'checks':checks,'passed':sum(x['pass'] for x in checks),'total':len(checks),'scope':'exact current-main cover compiler/schema/controller renewal control flow plus synthetic ammo observations; no live game/model/Executor/OS input'}
(ROOT/'results/cover_fire_probe.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2,sort_keys=True))

