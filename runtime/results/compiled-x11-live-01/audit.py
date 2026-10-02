"""Read-only finite acceptance census; source/image/task checks, not formal proof."""
import hashlib, json
from pathlib import Path
from PIL import Image

def require(condition,message):
    if not condition: raise ValueError(message)

def read(path): return json.loads(path.read_text())
def audit(root):
    results={}
    for name,count,outcome in [('positive',2,'TASK_SUCCEEDED'),('changed',1,'SAFE_YIELD')]:
        case=root/name; allocation=read(case/'allocation.json'); cleanup=read(case/'cleanup.json')
        require(cleanup['status']=='closed' and len(cleanup['child_exit_codes'])==2,'terminal cleanup missing')
        commands=[read(p) for p in sorted((case/'commands').glob('*.json'))]
        require([r['op'] for r in commands]==['observe','mint','mint','run','close'],'unexpected command inventory')
        receipt=read(case/'replies/004.json')['reply']
        require(receipt['outcome']==outcome and receipt['completed_transitions']==count,'wrong graph outcome')
        if name=='changed': require(receipt['reason']=='unknown_state','wrong changed stop')
        require(len(receipt['observations'])==count+1,'fresh intermediate observation inventory')
        raw=[read(p) for p in (case/'bridge').glob('compiled-*-execution.json')]
        require(len(raw)==count,'unexpected input/replay inventory')
        for row in raw:
            require(row['result']['status']=='completed','input not completed')
            require(row['request']['valid_until_ns']<=receipt['started_ns']+10_000_000_000,'method deadline renewed')
            releases=row['result']['execution']['releases']
            require(bool(releases) and all(r['verified'] and r['keys_down']==[] and r['buttons_down']==[] for r in releases),'nonneutral release')
        programs=[read(p) for p in (case/'bridge').glob('program-*.json')]
        require(len(programs)==count,'unexpected program inventory')
        deadlines={row['request']['valid_until_ns'] for row in raw}
        require(all(p['authority']['expires_at_ns'] in deadlines for p in programs),'program deadline lost')
        texts=[o['text'] for p in programs for o in p['ops'] if o['op']=='text']
        require(texts==[allocation['token']],'unexpected text/collateral program')
        initial=read(case/'bridge/observation-1.json')
        with Image.open(initial['native']['artifact']['path']) as opened:
            reference_image=opened.convert('RGB')
        boxes={c['alias']:(c['point'][0]-12,c['point'][1]-12,c['point'][0]+12,c['point'][1]+12) for c in commands if c['op']=='mint'}
        for graph_observation in receipt['observations']:
            native=read(case/'bridge'/f"observation-{graph_observation['sequence']}.json")
            artifact=native['native']['artifact']; image=Path(artifact['path'])
            require(hashlib.sha256(image.read_bytes()).hexdigest()==artifact['sha256']==graph_observation['evidence_digest'],'image identity mismatch')
            require(artifact['source_raw_sha256']==native['native']['sha256'],'capture identity mismatch')
            with Image.open(image) as opened:
                rgb=opened.convert('RGB'); color=rgb.getpixel((50,160))
                observed={'field_present':rgb.crop(boxes['field']).tobytes()==reference_image.crop(boxes['field']).tobytes(),
                          'submit_present':rgb.crop(boxes['save']).tobytes()==reference_image.crop(boxes['save']).tobytes(),
                          'field_accepted':color in ((40,180,60),(30,110,60)),'saved_cue':color==(30,110,60)}
            require(graph_observation['predicates']==observed,'predicates do not match original pixels')
        require(receipt['observations'][1]['predicates']['field_accepted'] is True,'no intermediate accepted cue')
        require(receipt['observations'][1]['predicates']['submit_present'] is (name=='positive'),'changed control not detected')
        events=[json.loads(line) for line in (case/'events.jsonl').read_text().splitlines()]
        saves=[e for e in events if e['event']=='save']
        require(saves==([{'event':'save','value':allocation['token'],'eligible':True}] if name=='positive' else []),'wrong independent Save outcome')
        require(events and [e for e in events if e['event']=='value_changed'][-1]['value']==allocation['token'],'wrong final field value')
        results[name]={'outcome':outcome,'completed_transitions':count,'graph_observations':len(receipt['observations']),
            'all_native_observations':len(list((case/'bridge').glob('observation-*.json'))),'input_programs':len(programs),
            'independent_save_count':len(saves),'method_elapsed_ns':receipt['elapsed_ns'],
            'fixed_wait_ms':sum(o['timeout_ms'] for p in programs for o in p['ops'] if o['op']=='wait_update'),
            'program_emissions':sum(row['result']['execution']['program_emissions'] for row in raw),
            'commands':len(commands),'child_exit_codes':cleanup['child_exit_codes']}
    return results

if __name__=='__main__': print(json.dumps(audit(Path(__file__).resolve().parent),indent=2))
