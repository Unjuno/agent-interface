"""One real Calc composition via the existing compiled API; no durable oracle."""
import csv, io, json, subprocess, time, hashlib
from pathlib import Path
from PIL import Image
from runtime.guarded_x11_v1 import compiled

def read_cells(rgb, regions, directory):
    directory.mkdir(exist_ok=False)
    rows={}
    for name,box in regions.items():
        crop=rgb.crop(box).resize(((box[2]-box[0])*4,(box[3]-box[1])*4),Image.Resampling.NEAREST)
        buf=io.BytesIO();crop.save(buf,format='PNG');payload=buf.getvalue()
        (directory/(name+'.png')).write_bytes(payload)
        start=time.monotonic_ns()
        p=subprocess.run(['tesseract','stdin','stdout','-l','eng','--psm','7','tsv'],input=payload,capture_output=True,timeout=2)
        end=time.monotonic_ns()
        (directory/(name+'.tsv')).write_bytes(p.stdout);(directory/(name+'.stderr')).write_bytes(p.stderr)
        words=[r for r in csv.DictReader(io.StringIO(p.stdout.decode()),delimiter='\t') if r.get('level')=='5' and r.get('text','').strip()]
        value=words[0]['text'] if p.returncode==0 and len(words)==1 and float(words[0]['conf'])>=90 else None
        rows[name]={'value':value,'words':words,'returncode':p.returncode,'started_ns':start,'ended_ns':end,'crop_sha256':hashlib.sha256(payload).hexdigest()}
    (directory/'reading.json').write_text(json.dumps(rows,indent=2)+'\n')
    return rows

def predicates(bridge,refs,native,rgb,rows):
    focused=bridge._focus_within_target()
    result={'present':rgb.crop(refs['sheet-context']['box']).tobytes()==refs['sheet-context']['pixels'],
            'main_focus':focused,'handoff':not focused}
    values=[rows[k]['value'] for k in ('A1','A2')]
    if all(v is not None for v in values):result['cells_match']=values==['317','529']
    return result

def run(bridge,refs,regions):
    if set(refs)!={'sheet-context'} or set(regions)!={'A1','A2'}:raise ValueError('exact grounded context and two regions')
    for box in regions.values():
        if type(box) is not list or len(box)!=4 or any(type(v) is not int for v in box) or not (0<=box[0]<box[2]<=1280 and 0<=box[1]<box[3]<=800):raise ValueError('bounded exact image regions')
    count=0;initial_scope=bridge.scope
    def perceive(native,rgb):
        nonlocal count
        count+=1
        rows=read_cells(rgb,regions,bridge.out/('calc-reading-'+str(count)))
        values=predicates(bridge,refs,native,rgb,rows)
        bridge._save('calc-predicates-'+str(count)+'.json',{'source_sequence':native['sequence'],'source_sha256':native['native']['artifact']['sha256'],'predicates':values,'scope':'visible cells and focus only; no saved effect'})
        return values
    def verify(payload,native,rgb):
        # The graph already checked cells_match using the exact same capture.
        # Focus leaving main does not establish a save or identify a new modal.
        return {'status':'succeeded' if payload['action']=='enter' else 'unavailable',
                'evidence_ref':payload['observation']['evidence_ref']}
    sym={'kind':'target_reference','target_reference':'sheet-context','identity_predicate':'present','dependencies':['present','main_focus']}
    interface={'format':'compiled-gui-interface-v1','interface_id':'calc-pixel-admission','session_scope':initial_scope,'surface':compiled.surface(bridge),
      'predicates':['present','main_focus','handoff','cells_match'],'symbols':{'sheet':sym},
      'actions':{'enter':{'target_symbol':'sheet','operation':'enter_two_cells','expected_effect':{'cells_match':True}},
                 'save':{'target_symbol':'sheet','operation':'request_save','expected_effect':{'handoff':True}}},
      'method':{'name':'enter-read-save-yield','version':'1','initial_state':'start','max_transitions':2,'max_runtime_ms':10000,'states':{
        'start':{'branches':[{'when':{'present':True,'main_focus':True},'outcome':'action','action':'enter','next_state':'filled','reason':None}]},
        'filled':{'branches':[{'when':{'cells_match':True,'present':True,'main_focus':True},'outcome':'action','action':'save','next_state':'handoff','reason':None}]},
        'handoff':{'branches':[{'when':{'handoff':True},'outcome':'yield','action':None,'next_state':None,'reason':'association_changed'}]}}}}
    bindings={
      'enter':{'interaction':'keyboard','offset':refs['sheet-context']['offset'],'tail':[
        {'op':'key_chord','keys':['CTRL','HOME']},{'op':'text','text':'317','gap_ms':20},{'op':'key_chord','keys':['ENTER']},
        {'op':'wait_update','timeout_ms':100},{'op':'text','text':'529','gap_ms':20},{'op':'key_chord','keys':['ENTER']},{'op':'wait_update','timeout_ms':100}]},
      'save':{'interaction':'keyboard','offset':refs['sheet-context']['offset'],'tail':[{'op':'key_chord','keys':['CTRL','s']}]}}
    raw=compiled.run(bridge,interface,bindings,perceive=perceive,verify_effect=verify)
    latest=bridge.history[bridge.sequence][0]
    return {'receipt':raw,'image_path':latest['native']['artifact']['path'],'image_sha256':latest['native']['artifact']['sha256'],
            'focused_candidate':bridge.focused_client_window(),'task_success':None,'scope':'graph mechanics; independent saved task still unscored'}
