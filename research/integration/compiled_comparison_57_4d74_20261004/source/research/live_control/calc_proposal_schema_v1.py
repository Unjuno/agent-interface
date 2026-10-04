"""Strict bounded proposal schema for isolated numeric Calc task; no coercion."""
import json


def validate(value):
    if type(value) is not dict: raise ValueError('object required')
    if type(value.get('rationale')) is not str or not 1 <= len(value['rationale']) <= 600:
        raise ValueError('bounded rationale required')
    kind = value.get('kind')
    if kind == 'verify':
        if set(value) != {'kind','rationale','visible_A1','visible_A2','confirmation_dialog_visible'}:
            raise ValueError('verify fields')
        if any(type(value[k]) is not int for k in ('visible_A1','visible_A2')):
            raise ValueError('numeric visible cells required')
        if type(value['confirmation_dialog_visible']) is not bool: raise ValueError('dialog boolean required')
    elif kind == 'stop':
        if set(value) != {'kind','rationale'}: raise ValueError('stop fields')
    elif kind == 'act':
        if set(value) != {'kind','rationale','steps'}: raise ValueError('act fields')
        steps=value['steps']
        if type(steps) is not list or not 1<=len(steps)<=10: raise ValueError('bounded steps required')
        for s in steps:
            if type(s) is not dict: raise ValueError('step object required')
            op=s.get('op')
            if op=='text':
                if set(s)!={'op','text'} or type(s['text']) is not str or not s['text'].isascii() or not s['text'].isdigit() or not 1<=len(s['text'])<=8:
                    raise ValueError('numeric text required')
            elif op=='key':
                if set(s)!={'op','key'} or s['key'] not in ('Return','Tab','Escape','Home','Up','Down','Left','Right'):
                    raise ValueError('unsupported key')
            elif op=='chord':
                if set(s)!={'op','modifier','key'} or s['modifier']!='Control_L' or s['key'] not in ('s','a','Home'):
                    raise ValueError('unsupported chord')
            elif op=='pointer_click':
                if (set(s)!={'op','x','y','duration_ms'} or type(s['x']) is not int or type(s['y']) is not int
                    or not 0<=s['x']<1280 or not 0<=s['y']<800 or type(s['duration_ms']) is not int or s['duration_ms']!=80):
                    raise ValueError('bounded pointer required')
            else: raise ValueError('unsupported step')
    else: raise ValueError('unknown kind')
    return value


def parse(raw):
    def unique(pairs):
        value={}
        for k,v in pairs:
            if k in value: raise ValueError('duplicate JSON key')
            value[k]=v
        return value
    return validate(json.loads(raw, object_pairs_hook=unique))
