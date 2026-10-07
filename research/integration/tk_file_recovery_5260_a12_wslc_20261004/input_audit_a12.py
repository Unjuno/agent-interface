"""A12 independent phase projections. No candidate/dispatch/gate producer imports.

Projection never changes the retained row. Whole-row pipe and file custody
must additionally be checked; a projected phase alone is not evidence of H.
"""
import copy
from drift_audit import phase_errors
from gate_audit import gate_errors
from sample_custody import sample_errors
from recovery_audit import recovery_errors
from effect_audit import effect_errors

def input_errors(row,fixture,freeze_sha):
    errors=[]
    try:
        if row['mode'] not in ('STABLE','DRIFT_REFUSE','DRIFT_RECOVER'):return ['unknown_a12_arm']
        inj=row['injection'];phase=inj['post_admission'];keys=inj['key_requests'];saves=inj['save_requests']
        initial=copy.deepcopy(row)
        if row['mode']=='DRIFT_RECOVER':
            initial['mode']='DRIFT_REFUSE'
            initial['injection'].update(key_requests=[],save_requests=[])
        errors.extend(gate_errors(initial,fixture,freeze_sha))
        errors.extend(sample_errors(initial))
        errors.extend(prior_errors(row,fixture,freeze_sha))
        for name in ('prior_emissions','total_emissions'):
            counts=phase[name]
            if any(type(counts[k]) is not int or counts[k]<0 for k in ('keys','saves')):
                errors.append('emission_count_types')
        if phase['total_emissions']!={'keys':len(keys),'saves':len(saves)}:errors.append('total_emission_counts')
        effective=copy.deepcopy(row)
        if row['mode']=='DRIFT_RECOVER':
            errors.extend(recovery_input_errors(row,fixture,freeze_sha))
            recovery=phase['recovery'];click=recovery['click'];effective['mode']='STABLE'
            effective['injection'].update(gate=copy.deepcopy(recovery['gate']),click_widget='target',
                click_started_ns=click['started_ns'],click_sync_returned_ns=click['completed_ns'],
                x=click['x'],y=click['y'])
        else:
            if phase['recovery'] is not None:errors.append('unexpected_recovery')
            if phase['prior_emissions']!=phase['total_emissions']:errors.append('unexplained_emissions')
        errors.extend(effect_errors(effective,fixture))
    except (KeyError,TypeError,ValueError,IndexError,AttributeError) as error:
        errors.append('malformed_a12_input:'+type(error).__name__)
    return errors

def recovery_input_errors(row,fixture,freeze_sha):
    errors=[]
    try:
        inj=row['injection'];phase=inj['post_admission'];recovery=phase['recovery']
        keys=inj['key_requests'];saves=inj['save_requests'];g=row['ready']['geometry']
        if phase['total_emissions']!={'keys':len(keys),'saves':len(saves)}:
            errors.append('total_emission_counts')
        stage={'requested':row['mode']=='DRIFT_RECOVER','prior':phase['prior'],
            'prior_keys':[],'prior_saves':[],'recovery':recovery,
            'keys':[{'char':k['char'],'started_ns':k['request_started_ns'],
                'completed_ns':k['sync_returned_ns']} for k in keys],
            'saves':[{'started_ns':s['request_started_ns'],'completed_ns':s['sync_returned_ns']} for s in saves]}
        errors.extend(recovery_errors(stage,fixture['payload']))
        click=recovery['click']
        if (any(type(click.get(axis)) is not int for axis in ('x','y')) or
            click['x']!=g['target_root_x']+g['target_width']//2 or
            click['y']!=g['target_root_y']+g['target_height']//2):errors.append('recovery_click_geometry')
        projected=copy.deepcopy(row);projected['mode']='STABLE'
        projected['injection'].update(gate=copy.deepcopy(recovery['gate']),click_widget='target',
            click_started_ns=click['started_ns'],click_sync_returned_ns=click['completed_ns'],
            x=click['x'],y=click['y'])
        errors.extend(gate_errors(projected,fixture,freeze_sha))
        errors.extend(sample_errors(projected))
    except (KeyError,TypeError,ValueError,IndexError,AttributeError) as error:
        errors.append('malformed_recovery_input:'+type(error).__name__)
    return errors

def prior_errors(row,fixture,freeze_sha):
    errors=[]
    try:
        phase=row['injection']['post_admission'];prior=phase['prior']
        projected=copy.deepcopy(row)
        projected['injection']['post_admission']=copy.deepcopy(prior)
        if row['mode']=='DRIFT_RECOVER':
            recovery=phase['recovery'];boundary=recovery['started_ns']
            end=prior['dispatch_completed_ns']
            if type(boundary) is not int or not end<=boundary:errors.append('recovery_before_refusal')
            if phase['prior_emissions']!={'keys':0,'saves':0}:errors.append('prior_emission_counts')
            requests=row['injection']['key_requests']+row['injection']['save_requests']
            if any(type(r['request_started_ns']) is not int or r['request_started_ns']<boundary
                   for r in requests):errors.append('request_before_recovery')
            effects=[e for e in row['app']['events'] if e.get('kind') in ('KeyPress','Save')]
            if any(type(e['monotonic_ns']) is not int or e['monotonic_ns']<boundary for e in effects):
                errors.append('effect_before_recovery')
            projected['mode']='DRIFT_REFUSE'
            projected['injection'].update(key_requests=[],save_requests=[])
            projected['app']['events']=[e for e in projected['app']['events']
                if e.get('kind') not in ('KeyPress','Save') or e['monotonic_ns']<boundary]
        errors.extend(phase_errors(projected,fixture,freeze_sha))
    except (KeyError,TypeError,ValueError,IndexError,AttributeError) as error:
        errors.append('malformed_prior:'+type(error).__name__)
    return errors
