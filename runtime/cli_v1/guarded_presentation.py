"""Opt-in normal guarded result projection; raw retained reports stay authoritative."""
from copy import deepcopy
import json

_GUARD_FIELDS = frozenset(('stage','observation_sequence','eligible','status','handle',
    'authority','reason','name','point','observed_box','binding_translation',
    'local_translation','sequence','valid_until_ns','patch_sha256','reference_kind',
    'private_registry_id_exposed'))
_TOP_FIELDS = frozenset(('operation','task_success','replay_allowed','status','result',
    'source','observation_report','feedback_status','session','image_status','image',
    'call_directory','call_id','retained_call','operation_invoked'))
_RESULT_FIELDS = frozenset(('status','admission','required_capabilities','execution',
    'recovery_required','guard_checks'))
_EXECUTION_FIELDS = frozenset(('started_ns','ended_ns','emissions','program_emissions',
    'observations','releases','waits','activations','completed_ops'))


def brief_guarded_report(view):
    """Shorten only known exact-match guards, keeping all other result fields intact.

    This is a lossy presentation with exact-call full retrieval, not a replacement
    for the retained report. Unknown extensions and failure evidence remain full.
    """
    full=deepcopy(view)
    full['presentation']={'requested':'brief','returned':'full',
                          'reason':'critical_or_unsupported_result'}
    try:
        result=view['result'];execution=result['execution'];guards=result['guard_checks']
        session=view['session']
        if (set(view)-_TOP_FIELDS or set(result)!=_RESULT_FIELDS or set(execution)!=_EXECUTION_FIELDS
            or view['operation']!='guarded_input' or view['status']!='completed'
            or view['task_success'] is not None or view['replay_allowed'] is not False
            or result['status']!='completed' or result['admission']!='accepted'
            or result['recovery_required'] is not False or view['feedback_status']!='captured'
            or view['image_status']!='image' or session.get('error') is not None
            or session['recovery_required'] is not False or session['review_required'] is not False
            or execution['observations']!=[] or execution['activations']!=[] or not execution['releases']
            or any(r['verified'] is not True or r['keys_down']!=[] or r['buttons_down']!=[] for r in execution['releases'])
            or any(w.get('completed') is not True or 'error' in w for w in execution['waits'])
            or any('error' in r for r in execution['releases'])
            or not isinstance(view['call_id'],str) or not view['call_id']):
            return full
        stages=[g['stage'] for g in guards]
        if stages not in (['before_admission','before_focus'],
                          ['before_admission','before_focus','before_move','before_press']):
            return full
        for guard in guards:
            if (set(guard)!=_GUARD_FIELDS or guard['status']!='VALID' or guard['eligible'] is not True
                or guard['reason']!='exact_region_match'
                or guard['binding_translation']!=[0,0] or guard['local_translation']!=[0,0]
                or guard['reference_kind']!='session_alias' or guard['private_registry_id_exposed'] is not False
                or type(guard['observation_sequence']) is not int):
                return full
        projected=deepcopy(view)
        projected['result'].pop('guard_checks')
        projected['result']['guard_summary']={
            'status':'all_valid_exact_region_match', 'count':len(guards),
            'checks':[{'stage':g['stage'],'observation_sequence':g['observation_sequence'],
                       'handle':g['handle'],'status':g['status']} for g in guards],
            'scope':'Detailed guard records omitted; no additional authority or task success.'}
        projected['presentation']={
            'requested':'brief','returned':'brief',
            'scope':'Normal exact-match guard projection; not lossless. All other fields are unchanged.',
            'omitted_guard_details':len(guards),
            'retrieve':{'tool':'interface_results','arguments':{
                'call_id':view['call_id'],'include_image':False,'detail':'full'}}}
        size=lambda row:len(json.dumps({k:v for k,v in row.items() if k!='image'},sort_keys=True,
                                       separators=(',',':'),allow_nan=False).encode('utf-8'))
        if size(projected)>=size(view):
            full['presentation']['reason']='not_smaller'
            return full
        return projected
    except (KeyError,TypeError,ValueError,AttributeError):
        return full