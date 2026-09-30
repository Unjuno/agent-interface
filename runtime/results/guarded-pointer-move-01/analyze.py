"""Recompute the limited two-task result from retained native/public evidence."""
import base64, hashlib, json
from pathlib import Path
from PIL import Image
import io

def require(ok, why):
    if not ok: raise ValueError(why)

def analyze(root):
    root = Path(root)
    trial = root/'trial-03'
    load = lambda p: json.loads(p.read_text())
    plan = load(trial/'PLAN.json')
    for name, digest in plan['hashes'].items():
        require(hashlib.sha256((trial/name).read_bytes()).hexdigest() == digest, 'plan hash '+name)
    require(load(trial/'build-manifest.json')['source_revision'] == plan['source'], 'build source')
    session = trial/'guarded-local/session'
    require(load(session/'allocation.json')['seed'] == plan['seed'], 'seed')
    require(load(session/'allocation.json')['source'] == plan['source'], 'allocation source')
    score = load(session/'evaluation-at-close.json')
    require(score['record_count'] == 2 and score['exact_counts'] == {
        'task-1':1, 'task-2':1, 'task-3':0, 'task-4':0, 'task-5':0, 'task-6':0}, 'independent score')
    require(score['unexpected'] == [] and score['duplicates'] == {} and
            score['missing'] == ['task-3','task-4','task-5','task-6'] and not score['success'], 'scope score')
    evidence = trial/'host-evidence'
    reviews = {r['call_id']:r for r in load(trial/'primary-review.json')['reviewed']}
    events = [json.loads(x) for x in (evidence/'host-events.jsonl').read_text().splitlines()]
    moves, clicks, images, inputs = [], [], 0, 0
    for attempt in range(1,18):
        request = load(evidence/f'request-{attempt}.json')
        reply = load(evidence/f'reply-{attempt}.json')
        require(reply['id'] == attempt and reply['status'] == 'returned' and not reply['result']['isError'], 'reply status')
        content = reply['result']['content']
        row = json.loads(next(x['text'] for x in content if x['type']=='text'))
        kinds = [e for e in events if e.get('attempt') == attempt]
        require([e['kind'] for e in kinds] == ['send_requested','reply_available','presentation_started','presentation_callbacks_completed'], 'presentation order')
        require(kinds[1]['reply_sha256'] == hashlib.sha256((evidence/f'reply-{attempt}.json').read_bytes()).hexdigest(), 'reply event hash')
        require(request['tool'] == reply['tool'] == kinds[0]['tool'], 'tool identity')
        for block in content:
            if block['type'] != 'image': continue
            images += 1
            source = row['source']; reviewed = reviews[row['call_id']]
            data = base64.b64decode(block['data'], validate=True)
            digest = hashlib.sha256(data).hexdigest()
            require(digest == source['native']['artifact']['sha256'] == reviewed['png_sha256'], 'delivered PNG hash')
            require(reviewed['primary_reviewed'] is True and reviewed['sequence'] == source['sequence'], 'primary review record')
            artifact = source['native']['artifact']['path'].split('/guarded-pointer-move-03/',1)[1]
            require((trial/artifact).read_bytes() == data, 'native and delivered PNG')
        if reply['tool'] != 'interface_guarded_input': continue
        inputs += 1
        result = row['result']; execution = result['execution']
        require(result['status'] == 'completed' and result['recovery_required'] is False, 'input completion')
        require(execution['releases'] and all(r['verified'] and not r['keys_down'] and not r['buttons_down'] for r in execution['releases']), 'neutral input')
        raw = load(session/'server'/row['call_id']/'report.json')
        checks = raw['result']['guard_checks']
        require(all(c['eligible'] is True and c['status']=='VALID' and c['reason']=='exact_region_match' for c in checks), 'exact guards')
        interaction = request['arguments'].get('interaction','click')
        if interaction == 'move':
            programs = list((session/'server').glob('guarded-session-*/program-*.json'))
            matching = [load(p) for p in programs if load(p)['source']['observation_seq'] == checks[0]['observation_sequence']]
            require(len(matching)==1, 'unique move program')
            ops = matching[0]['ops']
            require(ops == [{'op':'focus','target':'browser'},
                {'op':'pointer_move','frame':'screen_physical_px','x':376,'y':401},
                {'op':'wait_update','timeout_ms':100},{'op':'release_all'}], 'pointer-only program')
            require(execution['program_emissions']==1 and [c['stage'] for c in checks] == ['before_admission','before_focus','before_move'], 'move guards/emissions')
            off = 'e6bf6b7e5d01e75023e9bd87a941d3de13c2104c02833ebdf2ecbf83819a27ab'
            require(all(c['patch_sha256']==off for c in checks), 'off guard patch')
            png = next(b for b in content if b['type']=='image')
            crop = Image.open(io.BytesIO(base64.b64decode(png['data']))).convert('RGB').crop((364,394,388,408))
            hover = hashlib.sha256(crop.tobytes()).hexdigest()
            require(hover == '839eb2498bd1a0ff46532a7365058b4693f17fe579371e19f605cab1b7b4e2f2', 'hover capture')
            moves.append({'attempt':attempt,'feedback_ms':kinds[1]['host_monotonic_ms']-kinds[0]['host_monotonic_ms'],
                          'execution_ms':(execution['ended_ns']-execution['started_ns'])/1e6,'hover_rgb_sha256':hover})
        elif request['arguments']['alias'].startswith('save_hover'):
            require([c['stage'] for c in checks] == ['before_admission','before_focus','before_move','before_press'], 'click stages')
            require(all(c['patch_sha256']=='839eb2498bd1a0ff46532a7365058b4693f17fe579371e19f605cab1b7b4e2f2' for c in checks), 'new hover click guard')
            clicks.append({'attempt':attempt,'feedback_ms':kinds[1]['host_monotonic_ms']-kinds[0]['host_monotonic_ms']})
    require(len(moves)==len(clicks)==2 and images==9 and inputs==8 and len(reviews)==9, 'counts')
    close = json.loads(load(evidence/'reply-17.json')['result']['content'][0]['text'])
    require(close['status']=='closed' and close['release']['verified'] and not close['release']['keys_down'] and not close['release']['buttons_down'], 'neutral close')
    require(events[-1]['kind']=='transport_closed' and events[-1]['code']==0, 'relay terminal')
    terminal = load(trial/'process-terminal-v2.json')
    require(terminal['original_fixture_exit_code']==0 and terminal['relay_transport']['code']==0, 'original fixture terminal')
    require(load(root/'trial-01/construction-stop.json')['allocation_created'] is False, 'first stop')
    require(load(root/'trial-02/terminal.json')['status']=='STOP_FLAT_NAV_TARGET', 'second stop')
    return {'status':'PASS_SCOPED_GUARDED_POINTER_MOVE', 'source':plan['source'], 'public_calls':17,
            'delivered_primary_reviewed_images':images,'input_calls':inputs,'moves':moves,'clicks':clicks,
            'independent_exact_counts':score['exact_counts'],'fixture_children':load(session/'cleanup.json'),
            'scope':'Two A-layout tasks only; full integration and efficiency remain HOLD.'}
