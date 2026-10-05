"""Independent saved-only file quality; NOT a full method/provider auditor.

No producer imports, GUI, process execution, model parsing or input authority.
App receipts are cooperative evidence, not OS/server attestation.
"""
import hashlib
import json
from pathlib import Path
import sys


def read(path):
    return json.loads(Path(path).read_bytes())


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def score_arm(directory, *, wanted, initial_decoy):
    require(type(wanted) is str and bool(wanted) and type(initial_decoy) is str,
            'TASK_SCHEMA_INVALID')
    root = Path(directory)
    ready, app = read(root/'ready.json'), read(root/'app_result.json')
    for value in (ready, app):
        require(type(value) is dict and type(value.get('pid')) is int and value['pid'] > 0
                and type(value.get('token')) is str and bool(value['token']), 'IDENTITY_SCHEMA_INVALID')
    require(type(app.get('target')) is str and type(app.get('decoy')) is str, 'APP_TEXT_SCHEMA_INVALID')
    require(app['pid'] == ready['pid'] and app['token'] == ready['token'], 'APP_IDENTITY_MISMATCH')
    require(type(app['started_ns']) is int and type(app['ended_ns']) is int
            and app['started_ns'] < app['ended_ns'], 'APP_CLOCK_INVALID')
    events, saves = app['events'], app['saves']
    require(type(events) is list and type(saves) is list, 'APP_EVENTS_INVALID')
    require(all(type(event) is dict and event.get('widget') in ('target','decoy')
                and event.get('kind') in ('KeyPress','KeyRelease') for event in events),
            'EVENT_SCHEMA_INVALID')
    require(all(type(event.get('ns')) is int and app['started_ns'] <= event['ns'] <= app['ended_ns']
                for event in events), 'EVENT_CLOCK_INVALID')
    wrong = sum(event.get('widget') != 'target' for event in events)
    changed_decoy = app['decoy'] != initial_decoy
    task_file = root/'task_result.json'
    if not task_file.exists():
        require(not saves, 'SAVE_WITHOUT_FILE')
        return dict(quality='WRONG_RECIPIENT_INPUT' if wrong or changed_decoy else 'UNFINISHED_NO_FILE',
                    file_present=False, wrong_recipient_events=wrong, decoy_changed=changed_decoy)
    blob = task_file.read_bytes()
    value = json.loads(blob)
    require(type(value) is dict and type(value.get('pid')) is int and value['pid'] > 0
            and type(value.get('token')) is str and bool(value['token'])
            and type(value.get('text')) is str, 'FILE_SCHEMA_INVALID')
    require(value.get('schema') == 'issue5260-a15-task-file-v1'
            and value.get('pid') == ready['pid'] and value.get('token') == ready['token'],
            'FILE_IDENTITY_MISMATCH')
    require(len(saves) == 1 and saves[0].get('status') == 'saved', 'EXCLUSIVE_SAVE_COUNT_INVALID')
    saved = saves[0]
    require(type(saved.get('bytes')) is int and saved['bytes'] > 0
            and type(saved.get('sha256')) is str, 'SAVE_SCHEMA_INVALID')
    digest = hashlib.sha256(blob).hexdigest()
    require(saved.get('bytes') == len(blob) and saved.get('sha256') == digest, 'FILE_RECEIPT_MISMATCH')
    require(type(saved.get('started_ns')) is int and type(saved.get('completed_ns')) is int
            and app['started_ns'] <= saved['started_ns'] <= saved['completed_ns'] <= app['ended_ns'],
            'SAVE_CLOCK_INVALID')
    require(value.get('text') == app['target'], 'FILE_APP_EFFECT_MISMATCH')
    quality = ('WRONG_RECIPIENT_INPUT' if wrong or changed_decoy
               else 'EXACT_FILE' if value['text'] == wanted else 'WRONG_FILE')
    return dict(quality=quality, file_present=True, text=value['text'], sha256=digest,
                wrong_recipient_events=wrong, decoy_changed=changed_decoy)


def audit(root):
    root = Path(root)
    plan = read(root/'plan.json')
    rows = []
    for row in plan['rows']:
        directory = root/'candidate'/row['id']
        require(read(directory/'close.json')['errors'] == [], 'OWNED_CLEANUP_ERROR')
        arms = {arm:score_arm(directory/arm/'app', wanted=row['wanted'], initial_decoy=row['decoy'])
                for arm in ('control','guard')}
        control, guard = [read(directory/arm/'app'/'ready.json') for arm in ('control','guard')]
        require(control['pid'] != guard['pid'] and control['token'] != guard['token'],
                'PAIRED_APP_IDENTITY_COLLISION')
        rows.append(dict(id=row['id'], wanted=row['wanted'], arms=arms))
    return dict(schema='a15-independent-file-score-v1', scope='SAVED_FILE_QUALITY_ONLY', rows=rows,
                formal_allocation=plan.get('formal_allocation', False),
                provider_performance_claim=False, method_audit_complete=False)


if __name__ == '__main__':
    print(json.dumps(audit(sys.argv[1]), sort_keys=True))
