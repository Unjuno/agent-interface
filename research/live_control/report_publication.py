"""Private two-site consumer adapter; report custody grants no input authority."""
import json
import os
from pathlib import Path
from retention import write_report, read_report

REPORT_LIMIT = 1048576


def publish_report(report, directory):
    """Store the pre-metadata snapshot, then acknowledge a checked sidecar.

    A write error can leave files. UNCONFIRMED means do not advance the case
    loop, never that an earlier task effect did not happen. No retry occurs.
    The caller-owned plain directory is required; no crash-atomic guarantee.
    """
    stage = 'sidecar_precheck'
    try:
        sidecar = Path(directory) / 'report.retention.json'
        if sidecar.exists():
            raise FileExistsError('existing retention sidecar retained')
        stage = 'report_write_readback'
        receipt = write_report(report, directory, max_bytes=REPORT_LIMIT)
        result = {'status':'RETAINED', 'receipt':receipt,
                  'operation_invoked':False, 'grants_input_authority':False}
        data = (json.dumps(result, sort_keys=True, separators=(',',':'))+'\n').encode('utf-8')
        if len(data)>4096:
            raise ValueError('sidecar output limit')
        stage = 'sidecar_write_readback'
        with sidecar.open('xb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if sidecar.read_bytes()!=data:
            raise OSError('sidecar readback mismatch')
        return result
    except Exception as error:
        return {'status':'RETENTION_UNCONFIRMED', 'stage':stage,
                'error':{'type':type(error).__name__, 'message':str(error)},
                'operation_invoked':False, 'grants_input_authority':False}


def read_retained_report(directory):
    sidecar = Path(directory)/'report.retention.json'
    if not 0<sidecar.stat().st_size<=4096:
        raise ValueError('bounded sidecar')
    result = json.loads(sidecar.read_bytes())
    if (type(result) is not dict or set(result)!={'status','receipt','operation_invoked','grants_input_authority'}
            or result['status']!='RETAINED' or result['operation_invoked'] is not False
            or result['grants_input_authority'] is not False):
        raise ValueError('data-only retained sidecar')
    return read_report(directory,result['receipt'], max_bytes=REPORT_LIMIT)


import contextlib

@contextlib.contextmanager
def cleanup_guard(report, stage):
    try:
        yield
    except Exception as error:
        report.setdefault("cleanup_errors", []).append({"stage":stage,"type":type(error).__name__,"message":str(error)})
        report["status"] = "FAILED"
        report["passed"] = False
