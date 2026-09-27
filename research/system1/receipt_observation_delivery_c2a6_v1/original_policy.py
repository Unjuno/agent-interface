"""Reporting only: effect deadline and caller observation deadline are separate."""
from __future__ import annotations
from typing import Any

BINDING=('case_id','session','request','clock_id','start_ns','deadline_ns')

def describe(context: dict[str,Any], receipt: dict[str,Any] | None,
             journal: dict[str,Any] | None, read_return_ns: int,
             owner_pid: int) -> dict[str,Any]:
    result={'effect':'UNKNOWN','receipt_observation':'UNKNOWN',
            'input_authority':False,'retry_authority':False,'task_success':None}
    if type(read_return_ns) is not int or read_return_ns < context['start_ns']:
        return result
    if type(receipt) is not dict or type(receipt.get('context')) is not dict:
        return result
    if any(receipt['context'].get(k)!=context[k] for k in BINDING):
        return result
    if type(receipt.get('owner_pid')) is not int or receipt['owner_pid']!=owner_pid:
        return result
    sent=receipt.get('receipt_ns')
    if type(sent) is not int or not context['start_ns']<=sent<=read_return_ns:
        return result
    result['receipt_observation']=('OBSERVED_BY_DEADLINE' if read_return_ns<=context['deadline_ns'] else 'OBSERVED_LATE')
    if type(journal) is not dict or type(journal.get('context')) is not dict:
        return result
    if any(journal['context'].get(k)!=context[k] for k in BINDING):
        return result
    for key in ('owner_pid','status','commit_ns','payload_sha256'):
        if journal.get(key)!=receipt.get(key):
            return result
    if receipt['status']=='NO_COMMIT':
        if receipt['commit_ns'] is None and receipt['payload_sha256'] is None:
            result['effect']='NO_EFFECT'
        return result
    commit=receipt.get('commit_ns')
    if receipt['status']!='COMMITTED' or type(commit) is not int or not context['start_ns']<=commit<=sent:
        return result
    sha=receipt.get('payload_sha256')
    if not isinstance(sha,str) or len(sha)!=64 or any(c not in '0123456789abcdef' for c in sha):
        return result
    result['effect']='ON_TIME' if commit<=context['deadline_ns'] else 'LATE'
    return result
