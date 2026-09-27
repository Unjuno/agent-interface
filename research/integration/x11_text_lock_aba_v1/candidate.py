"""Reporting-only classifiers. No output here authorizes input or recovery."""

def lock_bracket(pre: dict, post: dict, execution: dict) -> str:
    """Deliberately insufficient comparator: boundary samples are not history."""
    if (execution.get('completed_ops') == [0, 1, 2]
            and execution.get('releases') and execution['releases'][-1].get('verified') is True
            and pre.get('locked_mods') == 0 and post.get('locked_mods') == 0):
        return 'CLAIM_EXACT_TEXT'
    return 'UNCONFIRMED_MODIFIER_STATE'


def verify_effect(contract: dict, observation: dict | None, execution: dict) -> dict:
    """Finite cooperative fixture contract, not a general GUI verification API."""
    out={'authority':'none','input_dispatched':False,'replay_permitted':False}
    status='HOLD_EFFECT_EVIDENCE'
    if not isinstance(observation,dict): return dict(out,status=status)
    if (type(contract.get('epoch')) is not int or type(contract.get('xid')) is not int
        or not isinstance(contract.get('session'),str) or not contract['session']
        or not isinstance(contract.get('requested'),str)):
        return dict(out,status=status)
    required={'session','epoch','xid','value','ns','complete','key_event_count','kind'}
    if not required<=set(observation): return dict(out,status=status)
    if (observation['session']!=contract['session']
        or type(observation['epoch']) is not int or observation['epoch']!=contract['epoch']
        or type(observation['xid']) is not int or observation['xid']!=contract['xid']
        or type(observation['ns']) is not int or type(execution.get('ended_ns')) is not int
        or observation['ns']<execution['ended_ns']
        or observation['kind']!='SNAPSHOT' or observation['complete'] is not True
        or type(observation['key_event_count']) is not int or observation['key_event_count']!=8
        or not isinstance(observation['value'],str)
        or execution.get('completed_ops')!=[0,1,2]
        or any(type(v) is not int for v in execution.get('completed_ops',[]))
        or not execution.get('releases') or execution['releases'][-1].get('verified') is not True):
        return dict(out,status=status)
    status='PASS_EXACT_VALUE' if observation['value']==contract['requested'] else 'FAIL_EXACT_VALUE'
    return dict(out,status=status)
