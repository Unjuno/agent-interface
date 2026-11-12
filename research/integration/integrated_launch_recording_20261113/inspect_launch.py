"""Read-only outer accounting inspection, never process-state inference."""
import json
from pathlib import Path

def inspect_launch(directory):
    root=Path(directory)
    result={'status':'incomplete','process_state':'unknown','replay_allowed':False,
            'usage':None,'task_success':None,'cleanup_status':'unverified'}
    records={}
    for name in ('attempt-start.json','attempt-terminal.json'):
        try:
            with (root/name).open('rb') as stream:
                data=stream.read(65537)
            if len(data)>65536: raise ValueError('record exceeds bound')
            row=json.loads(data)
            if type(row) is not dict: raise ValueError('record is not an object')
            records[name]=row
        except FileNotFoundError:
            continue
        except (OSError,ValueError):
            return {**result,'status':'invalid_record','error_file':name}
    start=records.get('attempt-start.json')
    terminal=records.get('attempt-terminal.json')
    if start is None:
        return {**result,'status':'invalid_record' if terminal else 'unavailable'}
    if (start.get('schema')!='integrated-launch-attempt-v1'
            or type(start.get('started_ns')) is not int
            or start.get('replay_allowed') is not False):
        return {**result,'status':'invalid_record'}
    if terminal is None: return result
    values=[terminal.get(k) for k in ('started_ns','ended_ns','elapsed_ns')]
    if (any(type(v) is not int for v in values)
            or values[0]!=start['started_ns'] or values[1]<values[0]
            or values[2]!=values[1]-values[0]
            or terminal.get('status') not in ('launcher_returned','launcher_raised')
            or terminal.get('replay_allowed') is not False):
        return {**result,'status':'invalid_record'}
    return {**result,'status':'terminal_recorded','launcher_status':terminal['status'],
            'elapsed_ns':values[2]}
