"""Read-only retained-mechanics audit. Never captures, dispatches or replays."""
import base64,hashlib,io,json
from pathlib import Path
from PIL import Image
import openpyxl
from cell_cue import cell_pair_cue
ORIGINAL=Path('/var/tmp/agent-interface-evidence-storage-main/results-local/calc-public-input-guard-live-01')

def need(condition,message):
    if not condition:raise ValueError(message)

def audit(root,*,read=None,verify_manifest=True):
    root=Path(root);read=read or (lambda relative:(root/relative).read_bytes())
    def load(relative):return json.loads(read(str(relative)))
    def blob_path(encoded):
        p=Path(encoded);need(p.is_relative_to(ORIGINAL),'unowned artifact path')
        return p.relative_to(ORIGINAL).as_posix()
    freeze=load('FREEZE.json')
    for name,digest in freeze['files'].items():need(hashlib.sha256(read(name)).hexdigest()==digest,'frozen source changed')
    for name,digest in freeze['runtime_files'].items():need(hashlib.sha256(read('runtime-source/'+name)).hexdigest()==digest,'frozen runtime source changed')
    if verify_manifest:
        for line in read('CURRENT-SHA256SUMS').decode().splitlines():
            digest,name=line.split('  ',1);need(hashlib.sha256(read(name)).hexdigest()==digest,'manifest mismatch: '+name)
    schedule=load('schedule.json');need([x['case'] for x in schedule]==['compiled-normal','compiled-wrong'],'schedule changed')
    block=load('BLOCK-RESULT.json');summary={x['case']:x for x in block['cases']};out=[]
    for row in schedule:
        name=row['case'];case=root/name;normal=row['second']=='864'
        def cjson(relative):return load(name+'/'+relative)
        directories=list((case/'public-owner').glob('guarded-session-*'));need(len(directories)==1,'one original owner required')
        bridge=directories[0];bridge_rel=bridge.relative_to(root).as_posix()
        native={}
        for path in bridge.glob('observation-*.json'):
            n=load(path.relative_to(root));a=n['native']['artifact'];data=read(blob_path(a['path']))
            need(hashlib.sha256(data).hexdigest()==a['sha256'] and len(data)==a['bytes'],'capture artifact identity mismatch')
            need(a['source_raw_sha256']==n['native']['sha256'],'raw capture association mismatch')
            rgb=Image.open(io.BytesIO(data)).convert('RGB');need(rgb.size==(1280,800),'capture geometry changed')
            native[n['sequence']]=(n,rgb)
        need(sorted(native)==list(range(1,(21 if normal else 11)+1)),'capture sequence changed')
        reports=[load(p.relative_to(root)) for p in bridge.glob('public-observation-*.json')]
        need(len(reports)==len(native) and all(x['status']=='returned' for x in reports),'capture ledger mismatch')
        replies=[load(p.relative_to(root)) for p in sorted((case/'replies').glob('*.json'))]
        need(len(replies)==(16 if normal else 11),'command budget/count mismatch')
        for reply in replies:
            need('error' not in reply,'unaccounted command exception')
            if reply.get('image'):
                im=reply['image'];n,_=native[im['sequence']]
                need(im['sha256']==n['native']['artifact']['sha256'],'returned image is not exact current source')
                feedback=reply['feedback'];data=base64.b64decode(feedback['image']['data'],validate=True)
                need(hashlib.sha256(data).hexdigest()==im['sha256'],'presented image bytes mismatch')
        reviews=[x['raw'] for x in replies if x['op']=='primary_review']
        need(len(reviews)==(4 if normal else 3),'primary review declarations changed')
        review_sources=[x['source_sequence'] for x in reviews]
        need(review_sources==([2,5,17,21] if normal else [2,5,11]),'primary review source order changed')
        handoffs=[x for x in replies if x['op']=='review_window']
        need(all(x['raw']['status']=='reviewed' for x in handoffs),'explicit modal/main review failed')
        scopes={x['raw']['review']['binding_revision']:x['raw']['review']['scope'] for x in handoffs}
        method=cjson('replies/009.json');receipt=method['raw']['method_receipt'];observations=receipt['observations']
        need(receipt['outcome']=='SAFE_YIELD' and receipt['reason']==('effect_unavailable' if normal else 'effect_failed'),'raw terminal relabeled')
        need(receipt['completed_transitions']==(2 if normal else 1),'completed prefix changed')
        need([x['sequence'] for x in observations]==([6,11,16] if normal else [6,11]),'method observation/source mismatch')
        need(observations[-1]['sequence']==method['image']['sequence'],'final feedback source mismatch')
        need(observations[0]['predicates']['blank'] is True and observations[1]['predicates']['cells_filled'] is normal,'input/effect semantic cue changed')
        ocr=cjson('method/ocr/002.json');need(ocr['sequence']==11 and ocr['artifact_sha256']==native[11][0]['native']['artifact']['sha256'],'OCR source mismatch')
        need(ocr['command']==['tesseract','stdin','stdout','--psm','11','tsv'] and ocr['returncode']==0 and ocr['source_context_verified'] is True,'OCR mode/context changed')
        tsv=read(name+'/method/ocr/002.tsv').decode();need(cell_pair_cue(tsv,main_sheet_reviewed=True,modal_present=False)==('filled' if normal else 'wrong'),'OCR glyph evidence contradicts cue')
        guards=cjson('method/guard-events.json')
        if normal:
            need(len(guards)==5 and guards[0]['event']=='armed' and guards[0]['source_sequence']==11 and guards[0]['renewal'] is False and guards[0]['authority_granted'] is False,'guard dependency changed')
            need([g['stage'] for g in guards[1:]]==['before_admission','before_focus','before_key_press:CTRL','before_key_press:s'],'Save semantic guard stages changed')
            regions=cjson('method/plan.json')['refs']['cell_regions'];source=native[11][1]
            for g in guards[1:]:
                need(g['eligible'] is True and g['reason'] is None,'Save dependency check failed')
                n,rgb=native[g['sequence']];need(n['pointer_binding']==native[11][0]['pointer_binding'],'Save binding changed')
                need(all(rgb.crop(box).tobytes()==source.crop(box).tobytes() for box in regions),'Save cell dependency pixels changed')
        else:need(guards==[],'wrong cells armed Save')
        result_rows=[load(p.relative_to(root)) for p in bridge.glob('result-*.json')]
        extra=[d for d in result_rows if 'additional_input_checks' in d]
        need(len(extra)==(1 if normal else 0),'public input guard result count changed')
        if normal:
            public=extra[0]['additional_input_checks']
            need([g['stage'] for g in public]==[g['stage'] for g in guards[1:]],'public input guard stages changed')
            for public_check,app_check in zip(public,guards[1:]):
                seq=public_check['observation_sequence'];n,_=native[seq]
                need(seq==app_check['sequence'] and public_check['eligible'] is True and public_check['authority_granted'] is False,'public input guard evidence changed')
                need(public_check['scope']==scopes[n['binding_revision']] and public_check['binding_revision']==n['binding_revision'],'public input guard scope changed')
                need(n['capture_ns']<=public_check['started_ns']<=app_check['checked_ns']<=public_check['ended_ns'],'public input guard timing/source changed')

        programs=[load(p.relative_to(root)) for p in bridge.glob('program-*.json')];need(len(programs)==(4 if normal else 2),'input program count changed')
        saves=[p for p in programs if any(op.get('op')=='key_chord' and op.get('keys')==['CTRL','s'] for op in p['ops'])]
        need(len(saves)==(1 if normal else 0),'Save request count changed')
        emissions=0
        for p in programs:
            dispatch=load(bridge_rel+'/public-dispatch-'+p['program_id']+'.json');d=dispatch['result'];e=d['execution']
            need(dispatch['status']=='returned' and d['status']=='completed' and d['recovery_required'] is False,'input terminal/recovery changed')
            need(type(e['program_emissions']) is int,'missing explicit per-program emissions')
            source_sequence=p['source']['observation_seq'];revision=p['source']['binding_revision']
            need(source_sequence in native and native[source_sequence][0]['binding_revision']==revision,'program source/revision changed')
            need(p['authority']['lease_id']==scopes[revision].replace(':','-'),'program scope changed')
            need(type(p['authority']['expires_at_ns']) is int and e['started_ns']<p['authority']['expires_at_ns'] and e['ended_ns']<=p['authority']['expires_at_ns'],'completed program outside recorded lease')
            emissions+=e['program_emissions']
            need(e['releases'] and all(x.get('verified') is True and x.get('keys_down')==[] and x.get('buttons_down')==[] for x in e['releases']),'program neutral release not verified')
        if normal:
            save_program=saves[0]
            public_dispatch=load(bridge_rel+'/public-dispatch-'+save_program['program_id']+'.json')['result']
            need(extra[0]['execution']==public_dispatch['execution'],'public guard result detached from Save dispatch')
            need(all(g['ended_ns']<save_program['authority']['expires_at_ns'] for g in extra[0]['additional_input_checks']),'public guard completed outside Save lease')
        need(emissions==(27 if normal else 21),'per-program emission count changed')
        close=cjson('close.json');need(close['status']=='closed' and close['release']['verified'] is True and close['release']['keys_down']==[] and close['release']['buttons_down']==[],'same-owner close/release changed')
        cleanup=cjson('cleanup.json');need(cleanup['remaining']==[],'owned child remains')
        score=cjson('post-terminal-score.json');need(score['status']==('PASS_POST_TERMINAL_PERSISTED_GOAL' if normal else 'PASS_POST_TERMINAL_CORRECT_REFUSAL') and score['original_owner_and_children_absent'] is True and score['original_exec_exit']==0,'post-terminal boundary missing')
        saved=read(name+'/saved.xlsx');need(hashlib.sha256(saved).hexdigest()==score['source_sha256'] and saved==read(name+'/primary-values.xlsx'),'independent source/snapshot identity mismatch')
        book=openpyxl.load_workbook(io.BytesIO(saved),data_only=True);cells={cell.coordinate:cell.value for sheet in book for line in sheet for cell in line if cell.value is not None}
        need(len(book.worksheets)==1,'unexpected collateral worksheet')
        need(cells==({'A1':731,'A2':864} if normal else {}),'independent saved cells contradict task/control')
        need(score['nonempty_cells']==cells,'score does not match workbook')
        s=summary[name];need(s['save_requests']==len(saves) and s['program_emissions']==emissions and s['accepted_physical_captures']==len(native),'published totals contradict raw ledger')
        out.append({'case':name,'normal_task_verified':normal,'wrong_refusal_verified':not normal,'captures':len(native),'program_emissions':emissions})
    return {'status':'PASS','cases':out,'scope':'retained artifact consistency and task/control scoring; no new GUI qualification or model latency/cost claim'}

if __name__=='__main__':
    print(json.dumps(audit(Path(__file__).resolve().parent),indent=2))
