"""Pure non-authoritative event-binding consumer. No scenario labels or I/O.
This is conditional on a complete trusted application journal, not authentication,
counterfactual causality or future exactly-once execution.
"""
from typing import Any

def valid_value(v: Any) -> bool:
    return (type(v) is dict and set(v)=={'saved','revision','payload'} and
            type(v['saved']) is bool and type(v['revision']) is int and
            type(v['payload']) is str)

def valid_request(q: Any) -> bool:
    return (type(q) is dict and set(q)=={'request_id','session','resource','epoch','value'} and
            all(type(q[k]) is str and bool(q[k]) for k in ('request_id','session','resource')) and
            type(q['epoch']) is int and q['epoch']>=0 and valid_value(q['value']))

def classify(q: Any, acceptance: Any, snapshot: Any) -> dict:
    result = {'state':'UNKNOWN','event':'UNKNOWN','complete_this_request':False,
              'grants_input_authority':False,'causal_necessity':'UNRESOLVED'}
    if not valid_request(q) or type(acceptance) is not dict or type(snapshot) is not dict:
        return result
    a,s = acceptance,snapshot
    if a.get('accepted') is not True or not valid_request(a.get('request')) or a['request'] != q:
        return result
    if type(a.get('instance')) is not str or not a['instance'] or type(a.get('floor')) is not int:
        return result
    if (type(s.get('schema')) is not int or s['schema']!=1 or s.get('instance')!=a['instance'] or
        type(s.get('epoch')) is not int or s['epoch']!=q['epoch'] or
        s.get('session')!=q['session'] or s.get('resource')!=q['resource'] or
        not valid_value(s.get('state'))):
        return result
    result['state'] = 'MATCH' if s['state']==q['value'] else 'DIFFERENT'
    if (s.get('complete') is not True or type(s.get('floor')) is not int or
        type(s.get('ceiling')) is not int or not 0<=s['floor']<=s['ceiling'] or
        s['floor']!=a['floor'] or type(s.get('events')) is not list or
        len(s['events'])!=s['ceiling']-s['floor']):
        return result
    prior = None
    related = []
    for offset, e in enumerate(s['events'],1):
        if (type(e) is not dict or set(e)!={'seq','request','before','after'} or
            type(e['seq']) is not int or e['seq']!=s['floor']+offset or
            not valid_request(e['request']) or not valid_value(e['before']) or
            not valid_value(e['after']) or e['after']!=e['request']['value']):
            return result
        if prior is not None and prior!=e['before']:
            return result
        prior = e['after']
        if e['request']['request_id']==q['request_id']: related.append(e)
    if prior is not None and prior!=s['state']:
        return result
    if any(e['request']!=q for e in related):
        result['event']='REQUEST_CONFLICT'
    elif len(related)>1:
        result['event']='APPLIED_MULTIPLE'
    elif related:
        result['event']='APPLIED_ONCE'
    else:
        result['event']='NOT_APPLIED_IN_WINDOW'
    result['complete_this_request'] = result['state']=='MATCH' and result['event']=='APPLIED_ONCE'
    return result
