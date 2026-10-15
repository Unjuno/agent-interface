import pathlib,json,hashlib,struct,ast
p=pathlib.Path(__file__).resolve().parent
def h(b):return hashlib.sha256(b).hexdigest()
manifest=json.loads((p/'PRE_RUN_MANIFEST.json').read_text())
for n,v in manifest.items():
 b=(p/n).read_bytes();assert len(b)==v['bytes'] and h(b)==v['sha256'],n
r=json.loads((p/'RUN_RECEIPT.json').read_text())
assert r['exit_code']==0 and not r['timeout'] and r['start_utc']<r['end_utc']
for key in ('stdout','stderr'):
 b=(p/(key+'.txt')).read_bytes();assert len(b)==r[key]['bytes'] and h(b)==r[key]['sha256']
names=[n.name for n in ast.walk(ast.parse((p/'actor.py').read_text())) if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')]
err=(p/'stderr.txt').read_text();assert len(names)==6 and 'Ran 6 tests' in err and '\nOK\n' in err
rows=[json.loads(s) for s in (p/'stdout.txt').read_text().splitlines()]
def check(rows):
 assert len(rows)==7
 wire=[x for x in rows if x['case']=='wire'];assert len(wire)==2
 for x in wire:
  b=bytes.fromhex(x['hex']);assert len(b)==36
  # Independent decoder; all unused bytes must be zero.
  assert b[:2]==bytes((132,2)) and struct.unpack('=H',b[2:4])[0]==9
  assert b[4]==(67 if x['press'] else 68) and b[5]==9 and b[35]==7
  assert b[6:35]==bytes(29) and x['target']==7
 by={x['case']:x for x in rows if x['case']!='wire'}
 assert by['core_negative']['target']==4
 assert by['switch']['target']==7 and by['ABA']['target']==7
 assert by['alias_negative']['server_target']==7 and by['alias_negative']['rejected_inputs']==9
 assert by['reuse_residual']['down_generation']=='original' and by['reuse_residual']['up_generation']=='replacement' and by['reuse_residual']['adoption']=='HOLD'
check(rows)
controls=[]
for label,case,key,value in [('wrong_target','switch','target',4),('wrong_wire_id','wire','hex',rows[0]['hex'][:-2]+'04'),('erase_generation_residual','reuse_residual','up_generation','original')]:
 copy=json.loads(json.dumps(rows))
 next(x for x in copy if x['case']==case)[key]=value
 (p/(label+'.json')).write_text(json.dumps(copy,indent=2),encoding='utf-8')
 try:check(copy)
 except AssertionError:controls.append(label)
 else:raise AssertionError('accepted control '+label)
result={'verified_source_members':len(manifest),'tests':6,'rows':7,'controls_rejected':controls,'scope':'data-only/source-derived inert wire construction; no native or production qualification','decision':'explicit stable ID bypasses ClientPointer in modeled branch; generation and ownership HOLD'}
(p/'READER_RESULT.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
