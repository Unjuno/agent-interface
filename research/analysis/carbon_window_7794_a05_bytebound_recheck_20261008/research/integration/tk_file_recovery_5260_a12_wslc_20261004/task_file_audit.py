"""Independent A12 ordinary-file checker: no producer or GUI imports."""
import hashlib
import json
from pathlib import Path

def file_errors(directory,row,expected_text):
    errors=[]
    try:
        path=Path(directory)/'task_result.json';app=row['app']
        if expected_text is None:
            if path.exists() or app.get('task_file') is not None or app.get('save_count')!=0:
                errors.append('refused_file_effect')
            return errors
        receipt=app['task_file'];blob=path.read_bytes();value=json.loads(blob)
        if type(row.get('app_pid')) is not int or row['app_pid']<=0:
            errors.append('identity_types')
        if (value.get('schema')!='issue5260-a12-task-file-v1' or
            value.get('token')!=row['token'] or type(value.get('pid')) is not int or
            value.get('pid')!=row['app_pid']):errors.append('file_identity')
        if value.get('text')!=expected_text:errors.append('task_value')
        if (value.get('text')!=app['saved_text'] or type(app['save_count']) is not int or
            app['save_count']!=1):errors.append('save_binding')
        if (receipt['path']!='task_result.json' or type(receipt['bytes']) is not int or
            receipt['bytes']!=len(blob) or receipt['sha256']!=hashlib.sha256(blob).hexdigest()):
            errors.append('file_bytes')
        saves=[e for e in app['events'] if e.get('kind')=='Save']
        if len(saves)!=1:errors.append('save_event_count')
        else:
            clocks=[saves[0]['monotonic_ns'],receipt['started_ns'],receipt['fsynced_ns'],
                    receipt['completed_ns'],app['ended_ns']]
            if any(type(t) is not int or t<=0 for t in clocks) or clocks!=sorted(clocks):
                errors.append('file_clock')
    except (KeyError,TypeError,ValueError,OSError,AttributeError) as error:
        errors.append('malformed_file:'+type(error).__name__)
    return errors
