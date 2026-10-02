"""Read-only reconstruction. Imports neither worker nor execution wrapper."""
import hashlib,json,sys,xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
PROFILES=[[1,0],[5,3],[10,6],[-5,-3]]
NS='{http://www.w3.org/2000/svg}'
def sha(b):return hashlib.sha256(b).hexdigest()
def red_bounds(path):
    im=Image.open(path).convert('RGB');w,h=im.size
    pts=[(i%w,i//w) for i,(r,g,b) in enumerate(list(im.get_flattened_data())) if r>200 and g<70 and b<70]
    if not pts:return None
    return [min(x for x,y in pts),min(y for x,y in pts),max(x for x,y in pts)+1,max(y for x,y in pts)+1]
def run(root,phase):
    errors=[];rows=[];checks=0
    def ck(ok,label):
        nonlocal checks
        checks+=1
        if not ok:errors.append(label)
    files=sorted((root/'data'/phase).glob('case*/raw/CASE.json'))
    ck(len(files)==(8 if phase=='formal' else 2),'case_count')
    if phase=='formal':
        for p,h in json.loads((root/'FREEZE.json').read_text())['files'].items():
            ck(sha((root/p).read_bytes())==h,'source:'+p)
    for pos,p in enumerate(files):
        name=p.parent.parent.name;prefix=name+':'
        try:
            rec=json.loads(p.read_text());proc=json.loads((p.parent.parent/'PROCESS.json').read_text());ev=rec['events']
            ck(rec['status']=='complete',prefix+'complete')
            ck(type(proc['exit']) is int and proc['exit']==0 and proc['timeout'] is False,prefix+'process_exit')
            ck(proc['worker_pid']==rec['pid'] and proc['start_ns']<proc['end_ns'],prefix+'process_identity')
            ck(proc['spec']==rec['spec'] and json.loads(proc['argv'][-1])==rec['spec'],prefix+'spec_binding')
            expected=PROFILES[pos if pos<4 else 7-pos] if phase=='formal' else [[2,1],[8,4]][pos]
            spec=rec['spec'];ck(spec['first']==expected,prefix+'first_offset')
            ck(spec['id']==(f'formal-{pos:02d}' if phase=='formal' else 'construction-'+str(pos)),prefix+'case_id')
            ck(type(spec['rep']) is int and spec['rep']==(pos//4 if phase=='formal' else -1),prefix+'rep')
            ck(spec['phase']==phase,prefix+'phase')
            ck(rec['authority']=='none' and rec['public_runtime_exercised'] is False,prefix+'authority')
            ck(rec['display_socket_absent'] and rec['auth_removed'] and 'cleanup_error' not in rec,prefix+'cleanup')
            for n,e in rec['process_exits'].items():
                ck(type(e['returncode']) is int and e['returncode']==(-15 if n=='inkscape' else 0),prefix+'exit:'+n)
                starts=[x for x in ev if x['kind']=='process_start' and x['name']==n]
                ends=[x for x in ev if x['kind']=='process_exit' and x['name']==n]
                ck(len(starts)==len(ends)==1 and starts[0]['pid']==ends[0]['pid']==e['pid'],prefix+'process_trace:'+n)
            ck(set(rec['process_exits'])=={'inkscape','openbox','xvfb'},prefix+'process_set')
            ck([e['index'] for e in ev]==list(range(len(ev))) and all(a['ns']<=b['ns'] for a,b in zip(ev,ev[1:])),prefix+'event_order')
            journal=[json.loads(x) for x in (p.parent/'EVENTS.jsonl').read_text().splitlines()]
            ck(journal==ev,prefix+'event_journal')
            task=[e for e in ev if e.get('role')=='task']
            moves=[e for e in task if e['kind']=='motion'];buttons=[e for e in task if e['kind']=='button']
            xy=rec['target_center'];offsets=[expected]+[[5*i,3*i] for i in range(3,11)]
            ck(len(moves)==9 and [[e['x']-xy[0],e['y']-xy[1]] for e in moves]==offsets,prefix+'motion_path')
            ck(len(task)==11 and [e['down'] for e in buttons]==[True,False],prefix+'button_path')
            ck(buttons[0]['index']<moves[0]['index']<moves[-1]['index']<buttons[1]['index'],prefix+'task_order')
            def neutral(s):return s['mask']&7936==0 and not any(bytes.fromhex(s['keymap_hex'])) and s['button1'] is False
            for k in ['expected_motor','observed_motor','posttask_motor','final_motor','cleanup_motor']:
                ck(neutral(rec[k]),prefix+'neutral:'+k)
            before=rec['expected_motor'];held=rec['held_motor'];after=rec['posttask_motor']
            ck(held['button1'] is True and held['mask']&256!=0,prefix+'held')
            ck([after['x']-before['x'],after['y']-before['y']]==[50,30],prefix+'pointer_endpoint')
            ck(len(rec['steps'])==9,prefix+'step_count')
            for j,s in enumerate(rec['steps']):
                ck([s['x']-xy[0],s['y']-xy[1]]==offsets[j] and s['button1'] is True and s['focus']==before['focus'],prefix+f'step:{j}')
            for e in [x for x in ev if x['kind']=='image']:
                raw=(p.parent/e['name']).read_bytes();im=Image.open(p.parent/e['name']).convert('RGB')
                ck(sha(raw)==e['sha256'] and len(raw)==e['bytes'] and sha(im.tobytes())==e['pixel_sha256'],prefix+'image:'+e['name'])
                ck(list(im.size)==[e['width'],e['height']],prefix+'image_size')
            br=(p.parent/'before.svg').read_bytes();ar=(p.parent/'after.svg').read_bytes()
            ck(sha(br)==rec['before_sha256'] and sha(ar)==rec['after_sha256'],prefix+'svg_hash')
            b=ET.fromstring(br);a=ET.fromstring(ar);rb=b.find(NS+'rect');ra=a.find(NS+'rect')
            shapes=[n for n in a.iter() if n.tag in {NS+x for x in ['rect','path','circle','ellipse','polygon','polyline','text','image','use']}]
            ck(len(shapes)==1 and ra.attrib['id']=='r' and 'transform' not in ra.attrib,prefix+'only_original_shape')
            ck([float(rb.attrib[k]) for k in ['x','y','width','height']]==[50,50,40,30],prefix+'original_geometry')
            ck([float(ra.attrib[k]) for k in ['width','height']]==[40,30],prefix+'dimensions')
            delta=[float(ra.attrib[k])-float(rb.attrib[k]) for k in ['x','y']]
            bb=red_bounds(p.parent/'pre_task.png');fin=red_bounds(p.parent/'final.png')
            ck(bb is not None and fin is not None,prefix+'visible_target')
            ck(all(abs(v-w)<=1 for v,w in zip([bb[2]-bb[0],bb[3]-bb[1]],[40,30])),prefix+'one_to_one_scale')
            pixel_delta=[fin[i]-bb[i] for i in (0,1)]
            ck(all(abs(delta[i]-pixel_delta[i])<=1 for i in (0,1)),prefix+'saved_visible_parity')
            steps=[]
            for j in range(9):
                q=red_bounds(p.parent/f'step{j}.png');ck(q is not None,prefix+'visible_step')
                steps.append([q[i]-bb[i] for i in (0,1)])
            model=[50-expected[0],30-expected[1]]
            rows.append({'id':spec['id'],'rep':spec['rep'],'first':expected,'pointer_delta':[50,30], 'svg_delta':delta,'pixel_delta':pixel_delta,'step_pixel_deltas':steps,'simple_model_delta':model,'simple_model_match':all(abs(delta[i]-model[i])<=.25 for i in (0,1))})
        except Exception as exc:errors.append(prefix+'RAW_UNREADABLE:'+repr(exc))
    primary=False
    if phase=='formal' and len(rows)==8:
        primary=all(len({tuple(r['svg_delta']) for r in rows if r['rep']==rep})>=2 for rep in (0,1))
    decision='HOLD_INCOMPLETE_OR_INTEGRITY' if errors else ('PASS_FIRST_MOTION_DEPENDENCE_SCOPED' if primary else ('CONSTRUCTION_RECONSTRUCTED' if phase!='formal' else 'HOLD_NO_FIRST_MOTION_DISCRIMINATOR'))
    return {'decision':decision,'checks':checks,'errors':errors,'cases':len(rows),'simple_model_matches':sum(r['simple_model_match'] for r in rows),'rows':rows}
if __name__=='__main__':
    r=run(Path(sys.argv[1]),sys.argv[2]);print(json.dumps(r,sort_keys=True,indent=2));raise SystemExit(0 if not r['errors'] else 2)
