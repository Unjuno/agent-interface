import hashlib,json,pathlib,xml.etree.ElementTree as E,sys
R=pathlib.Path(__file__).resolve().parent;D=R/'runs/cache03';raw=json.loads((D/'raw.json').read_text());ns={'t':'urn:oasis:names:tc:opendocument:xmlns:table:1.0','o':'urn:oasis:names:tc:opendocument:xmlns:office:1.0'}
def effect(blob):
 table=E.fromstring(blob).find('.//t:table',ns);rows=table.findall('t:table-row',ns);cells=rows[1].findall('t:table-cell',ns)
 return [cells[i].get('{'+ns['o']+'}value') for i in range(3)]+[cells[2].get('{'+ns['t']+'}formula')]
errors=[];reports=[]
for task in raw['tasks']:
 p=D/(task['label']+'.fods');blob=p.read_bytes();actual=effect(blob);expected=[str(task['a']),str(task['b']),str(task['a']*task['b']),'of:=[.A2]*[.B2]'];bad=[]
 if actual!=expected:bad.append('saved document effect mismatch')
 if hashlib.sha256(blob).hexdigest()!=task['saved_sha256']:bad.append('saved byte identity')
 if task['physical']['keys'] or task['physical']['buttons']:bad.append('physical input not neutral')
 if task['receipt']['status']!='completed':bad.append('native receipt not completed')
 artifact=task['image']['image']['artifact'];png=D/'images'/pathlib.Path(artifact['path']).name
 if hashlib.sha256(png.read_bytes()).hexdigest()!=artifact['sha256']:bad.append('original PNG identity')
 reports.append(dict(label=task['label'],actual=actual,expected=expected,errors=bad));errors.extend(bad)
if [x['label'] for x in raw['tasks']]!=['cold','warm','repair','warm-after-repair']:errors.append('task inventory')
stale=[g for g in raw['guard_attempts'] if g['label']=='stale']
if len(stale)!=1 or stale[0]['decision']!='STALE_GEOMETRY' or stale[0]['input_dispatches']!=0:errors.append('stale guard pre-input record')
if (D/'stale.fods').exists():errors.append('unexpected stale document')
if raw['errors'] or raw['cleanup_physical']['keys'] or raw['cleanup_physical']['buttons']:errors.append('producer/cleanup')
out=dict(scope='construction only; saved bytes and recorded guard/physical observations; no provider/model/comparison claims',model_calls=0,errors=errors,tasks=reports,stale_dispatches=stale[0]['input_dispatches'] if len(stale)==1 else None)
(R/'CONSTRUCTION_ORACLE.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out));sys.exit(bool(errors))
