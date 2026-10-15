"""Data-only independent binary/raw reader; does not import producer/backend."""
import pathlib,json,hashlib,struct,ast
P=pathlib.Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
records={}
for label,expected in [('V4-FIRST',(4,1,1,1)),('MARKER-FIXED',(1,0,0,0))]:
    dest=P/label;r=json.loads((dest/'RESULT.json').read_text());start=json.loads((dest/'START.json').read_text())
    assert r['pid']==start['pid'] and r['supervisor_pid']==start['supervisor_pid'] and r['start']==start['start']
    assert r['start']<r['end'] and r['exit']==expected[3] and not r['timeout'] and r['pins_unchanged']
    for f,v in r['pins'].items():
        b=pathlib.Path(f).read_bytes();assert len(b)==v['bytes'] and sha(b)==v['sha256'],f
    for n,v in r['streams'].items():
        b=(dest/n).read_bytes();assert len(b)==v['bytes'] and sha(b)==v['sha256'],n
    rows=[json.loads(l) for l in (dest/'stdout.txt').read_text().splitlines()]
    summary=rows[-1];assert (summary['tests'],summary['failures'],summary['errors'])==expected[:3] and summary['forbidden']==[]
    err=(dest/'stderr.txt').read_text()
    assert f'Ran {expected[0]} test' in err
    records[label]=rows
assert 'TypeError: types.SimpleNamespace() argument after ** must be a mapping, not DictWrapper' in (P/'V4-FIRST'/'stderr.txt').read_text()
assert 'test_suppressed_stubborn_must_not_clear_custody' in (P/'V4-FIRST'/'stderr.txt').read_text()
assert sha((P/'source/runtime/backends/x11_v1/backend.py').read_bytes())=='4bc5aa463d5f5fd45f9e6eb8656e4093d94434329ba45aa268644e6e6a57c676'
first_ast=ast.parse((P/'actor.py').read_text());fixed_ast=ast.parse((P/'actor_fixed.py').read_text())
def methods(tree):return {n.name:ast.dump(n,include_attributes=False) for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')}
assert methods(first_ast)==methods(fixed_ast) and len(methods(first_ast))==4
# Only low-level property parser dict conversion + selector changed in repair.
first=(P/'actor.py').read_text();fixed=(P/'actor_fixed.py').read_text()
assert fixed==first.replace('PROPERTY_REPLY.parse_binary(raw,None)','PROPERTY_REPLY.parse_binary(raw,None,rawdict=True)').replace('unittest.defaultTestLoader.loadTestsFromTestCase(Tests)',"unittest.TestSuite([Tests('test_fixed_XTEST_marker_is_not_generation_identity')])")
sources={n:(P/'reference'/n).read_text() for n in ['xiquerydevice.c','queryst.c','xiquerypointer.c','xtest.c']}
assert 'rc = XaceHook(XACE_DEVICE_ACCESS, client, dev, DixReadAccess);' in sources['xiquerydevice.c']
assert 'ListButtonInfo(dev, (xXIButtonInfo *) any, rc == Success)' in sources['xiquerydevice.c']
assert 'memset(bits, 0, mask_len * 4);' in sources['xiquerydevice.c'] and 'if (reportState)' in sources['xiquerydevice.c']
assert 'if (rc != Success && rc != BadAccess)' in sources['queryst.c'] and 'if (rc != BadAccess)\n            memcpy(tb->buttons' in sources['queryst.c']
assert 'DixReadAccess);\n    if (rc != Success)' in sources['xiquerypointer.c']
assert 'return BadAccess;' in sources['xtest.c'] and 'XA_INTEGER, 8, PropModeReplace, 1, &dummy' in sources['xtest.c']

def inventory(raw):
    b=bytes.fromhex(raw);assert b[0]==1 and len(b)==32+struct.unpack_from('=I',b,4)[0]*4
    assert struct.unpack_from('=H',b,8)[0]==1
    did,use,attach,nclass,namelen,enabled,pad=struct.unpack_from('=HHHHHBB',b,32)
    assert enabled==1 and nclass==1
    off=44+namelen+(-namelen)%4
    typ,length,src,count=struct.unpack_from('=HHHH',b,off)
    assert typ==1 and count==10 and length*4==len(b)-off
    mask=int.from_bytes(b[off+8:off+12],'little')
    return {'device':did,'use':use,'attachment':attach,'sourceid':src,'mask':mask}

def verify(data):
    first=data['V4-FIRST'];fixed=data['MARKER-FIXED']
    by={x['case']:x for x in first if 'case' in x}
    a=by['visible_stubborn'];b=by['suppressed_stubborn']
    assert a['synthetic_source_buttons']==b['synthetic_source_buttons']==[9]
    assert a['reply']['status']=='release_unverified' and a['owned']==['x2'] and a['quarantine']
    assert b['reply']['status']=='completed' and b['owned']==[] and not b['quarantine']
    assert a['events']==b['events'] and a['emissions']==b['emissions']==3
    assert inventory(a['query_packets'][0])['mask']==1<<9
    assert inventory(b['query_packets'][0])['mask']==0
    witness=by['XI1_indistinguishable'];neutral=bytes.fromhex(witness['neutral_hex']);suppressed=bytes.fromhex(witness['suppressed_hex']);visible=bytes.fromhex(witness['visible_hex'])
    assert neutral==suppressed and len(neutral)==68 and neutral[1]==30 and neutral[8]==1
    assert struct.unpack_from('=I',neutral,4)[0]==9 and neutral[32:36]==bytes((1,36,10,0))
    assert int.from_bytes(neutral[36:68],'little')==0 and int.from_bytes(visible[36:68],'little')==1<<9
    marker=fixed[0];assert marker['case']=='generation_marker_indistinguishable' and marker['adoption']=='HOLD'
    obs=marker['observations'];assert len(obs)==2 and obs[0]['generation_scorer_only']!=obs[1]['generation_scorer_only']
    assert obs[0]['inventory_hex']==obs[1]['inventory_hex'] and obs[0]['marker_hex']==obs[1]['marker_hex']
    assert inventory(obs[0]['inventory_hex'])=={'device':7,'use':3,'attachment':2,'sourceid':7,'mask':0}
    b=bytes.fromhex(obs[0]['marker_hex']);assert len(b)==36 and struct.unpack_from('=III',b,8)==(19,0,1) and b[20]==8 and b[32:]==b'\1\0\0\0'
verify(records)
controls=[]
for name in ['erase_held_state','mask_no_longer_suppressed','hide_generation_reuse']:
    clone=json.loads(json.dumps(records))
    if name=='erase_held_state':next(x for x in clone['V4-FIRST'] if x.get('case')=='suppressed_stubborn')['synthetic_source_buttons']=[]
    elif name=='mask_no_longer_suppressed':
        rows={x['case']:x for x in clone['V4-FIRST'] if 'case' in x};rows['suppressed_stubborn']['query_packets']=rows['visible_stubborn']['query_packets']
    else:clone['MARKER-FIXED'][0]['observations'][1]['generation_scorer_only']='original'
    (P/(name+'.json')).write_bytes((json.dumps(clone,indent=2)+'\n').encode())
    try:verify(clone)
    except AssertionError:controls.append(name)
    else:raise AssertionError('control accepted '+name)
result={'actors_verified':2,'first':{'tests':4,'failures':1,'errors':1,'counterexample':'held9; V4completed/custodyclear; valid zero XI2 inventory'},'marker_repaired':{'tests':1,'failures':0,'errors':0,'original_other_methods_rerun':False},'copied_controls_rejected':controls,'scope':'source-supported XACE suppression/inert V4 construction; no native configuration or effect qualification','decision':'V4 stays non-adoptable; XI1 state query and XTEST marker do not supply missing permission/generation proof'}
(P/'READER_RESULT.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps(result))
