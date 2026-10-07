"""Independent stage consistency check, NOT full pipe or application custody.

No producer imports. Full audit must additionally reconstruct ACK from raw
pipe bytes, request counts from injection traces and effects from app/file.
STOP is accepted here only as an effect-free stop, never as task success.
"""
def recovery_errors(row,payload):
    errors=[]
    try:
        recovery=row['recovery'];keys=row['keys'];saves=row['saves']
        if recovery['status']=='STOP':
            if keys or saves:errors.append('stopped_recovery_effect')
            return errors
        if (recovery['status']!='EMITTED' or recovery['reason']!='NEW_RECOVERY_ADMISSION' or
            row['requested'] is not True or recovery['requested'] is not True):
            errors.append('explicit_recovery_contract')
        prior=row['prior']
        if (prior['dispatch']!={'status':'REFUSED','reason':'OBSERVED_DRIFT'} or
            prior['drift']['status']!='OBSERVED_DRIFT' or row['prior_keys'] or row['prior_saves'] or
            recovery['prior_emissions']!={'keys':0,'saves':0}):errors.append('prior_refusal')
        click=recovery['click'];gate=recovery['gate'];ack=gate['ack']
        if click['widget']!='target' or gate['status']!='ADMITTED':errors.append('new_target_admission')
        sequence=prior['drift']['frames'][-1]['sequence']
        if (type(sequence) is not int or type(ack['sequence']) is not int or
            sequence<=0 or ack['sequence']<=sequence):errors.append('new_sequence')
        clocks=[recovery['started_ns'],click['started_ns'],click['completed_ns'],
                gate['decided_ns'],recovery['dispatch_started_ns']]
        if (type(ack['event_ns']) is not int or
            not click['started_ns']<=ack['event_ns']<=gate['decided_ns']):errors.append('new_ack_clock')
        if ''.join(k['char'] for k in keys)!=payload or len(saves)!=1:errors.append('single_payload_save')
        for request in keys+saves:
            clocks.extend([request['started_ns'],request['completed_ns']])
        clocks.append(recovery['dispatch_completed_ns'])
        if any(type(t) is not int or t<=0 for t in clocks) or clocks!=sorted(clocks):
            errors.append('recovery_clock')
    except (KeyError,TypeError,ValueError,IndexError,AttributeError) as error:
        errors.append('malformed_recovery:'+type(error).__name__)
    return errors
