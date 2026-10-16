"""Bounded caller-declared contracts for the existing artifact sampler."""
import json,re


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)


def validate(value):
    if type(value) is not dict or set(value)!={'kind','expected'}:
        raise ValueError('explicit artifact contract required')
    expected=value['expected']
    if value['kind']=='saved_cells':
        if type(expected) is not dict or not 1<=len(expected)<=16:
            raise ValueError('1..16 declared cells required')
        for address,scalar in expected.items():
            if type(address) is not str or not re.fullmatch('[A-Z]{1,3}[1-9][0-9]{0,6}',address):
                raise ValueError('single uppercase cell address required')
            letters=re.match('[A-Z]+',address).group();column=0
            for letter in letters:column=column*26+ord(letter)-64
            if column>16384 or int(address[len(letters):])>1048576:
                raise ValueError('cell outside worksheet bounds')
            if type(scalar) not in (int,float,str,type(None)) or (type(scalar) is str and len(scalar)>1024):
                raise ValueError('bounded scalar cell value required')
    elif value['kind']=='saved_form_value':
        if type(expected) is not str or len(expected)>1024:raise ValueError('bounded expected form value required')
    else:raise ValueError('unsupported artifact contract')
    return json.loads(canonical(value))


def valid_reply(record,contract,request_id):
    """Checks protocol evidence, never authorizes input or asserts whole task success."""
    if (record.get('event')!='effect_checkpoint' or record.get('transport_request_id')!=request_id or
            record.get('command_op')!='effect_checkpoint' or record.get('authority')!='none' or
            record.get('task_success','missing') is not None):return False
    if record.get('status')=='UNKNOWN' and record.get('reason')=='verifier_busy' and 'evidence' not in record:
        return True
    evidence=record.get('evidence')
    if (type(evidence) is not dict or evidence.get('authority')!='none' or
            evidence.get('observation_closed') is not False or evidence.get('task_success','missing') is not None or
            canonical(evidence.get('contract'))!=canonical(contract)):return False
    if evidence.get('status')=='UNKNOWN':return True
    if evidence.get('status')!='VERIFIED':return False
    expected=contract['expected'] if contract['kind']=='saved_cells' else {'value':[contract['expected']]}
    return (canonical(evidence.get('actual'))==canonical(expected) and
            type(evidence.get('artifact_sha256')) is str and
            re.fullmatch('[0-9a-f]{64}',evidence['artifact_sha256']) is not None)
