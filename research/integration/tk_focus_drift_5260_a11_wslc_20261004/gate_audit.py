"""A11 initial admission audit derived from A09; later refusal is separate."""
def gate_errors(row,fixture,freeze_sha256):
    errors=[]
    try:
        injection=row['injection'];gate=injection['gate'];mode=row['mode']
        if mode not in ('STABLE','DRIFT_STALE_CONTROL','DRIFT_REFUSE'):
            return ['unknown_mode']
        click=injection['click_started_ns'];sync=injection['click_sync_returned_ns']
        if type(click) is not int or type(sync) is not int or not 0<click<=sync:
            errors.append('click_clock')
        expected_widget='target'
        if injection['click_widget']!=expected_widget:errors.append('click_widget')
        if mode=='NOW_TARGET':
            if gate.get('mode')!='NO_ACK_CONTROL' or gate['status']!='ADMITTED' or gate['ack'] is not None:
                errors.append('now_gate')
            if not sync<=gate['decided_ns']:errors.append('now_clock')
            return errors
        started,deadline,decided=gate['started_ns'],gate['deadline_ns'],gate['decided_ns']
        if (any(type(t) is not int for t in (started,deadline,decided)) or
                not sync<=started<=decided or deadline!=started+fixture['ack_timeout_ms']*1_000_000):
            errors.append('gate_clock')
        samples=gate['samples'];reads=row['pipe']['reads']
        if not samples:return errors+['missing_samples']
        previous=started;previous_count=0
        for sample in samples:
            checked=sample['checked_ns'];count=sample['read_attempts']
            if (type(checked) is not int or type(count) is not int or
                    not previous<=checked<=decided or not previous_count<=count<=len(reads) or count<=0):
                errors.append('sample_clock_or_count');continue
            if reads[count-1]['completed_ns']>checked:errors.append('sample_before_read')
            available=[frame for frame in row['pipe']['frames'] if frame['seen_ns']<=reads[count-1]['completed_ns']]
            latest=available[-1] if available else None
            state=latest['value'] if latest else None
            if sample['state']!=state or sample['seen_ns']!=(latest['seen_ns'] if latest else None):
                errors.append('sample_latest_frame')
            if sample['state'] is not None and any(type(sample['state'].get(name)) is not int
                    for name in ('pid','target_id','sequence','event_ns','written_ns')):
                errors.append('sample_receipt_types')
            wanted=[]
            if state is None:wanted=['no_frame']
            else:
                if (state.get('schema')!='issue5260-a09-focus-pipe-v1' or
                        state.get('token')!=row['token'] or state.get('pid')!=row['app_pid'] or
                        state.get('target_id')!=row['ready']['geometry']['target_id'] or
                        state.get('freeze_sha256')!=freeze_sha256):wanted.append('source_binding')
                if any(type(state.get(name)) is not int or state[name]<=0
                       for name in ('pid','target_id','sequence','event_ns','written_ns')):
                    wanted.append('receipt_types')
                else:
                    if state.get('kind')!='FocusIn' or state.get('widget')!='target' or state.get('focus_get')!='target':
                        wanted.append('not_current_target')
                    if not click<=state['event_ns']<=state['written_ns']<=checked:wanted.append('receipt_clock_order')
                    if checked-state['written_ns']>fixture['ack_max_age_ms']*1_000_000:wanted.append('receipt_expired')
            if sample['errors']!=wanted:errors.append('sample_error_binding')
            previous=checked;previous_count=count
        last=samples[-1]
        if last['checked_ns']!=decided or gate['state']!=last['state']:errors.append('decision_sample')
        if gate['status']=='ADMITTED':
            if not isinstance(gate['ack'],dict) or any(type(gate['ack'].get(name)) is not int
                    for name in ('pid','target_id','sequence','event_ns','written_ns')):
                errors.append('ack_receipt_types')
            if (last['errors'] or decided>deadline or gate['ack']!=last['state'] or
                    gate['reason']!='CURRENT_TARGET_RECEIPT'):errors.append('invalid_admission')
            if (mode!='DRIFT_REFUSE' and not injection['key_requests'] or
                injection['key_requests'] and injection['key_requests'][0]['request_started_ns']<decided):
                errors.append('key_before_admission')
        elif gate['status']=='REFUSED':
            if gate['ack'] is not None or injection['key_requests'] or injection['save_requests']:
                errors.append('refused_input')
            if gate['reason']=='TIMEOUT':
                if decided<deadline:errors.append('early_timeout')
            elif gate['reason']=='EOF_BEFORE_ADMISSION':
                if not any(read['status']=='EOF' for read in reads[:last['read_attempts']]):errors.append('unobserved_eof')
            else:errors.append('refusal_reason')
        else:errors.append('gate_status')
    except (KeyError,TypeError,ValueError,IndexError,AttributeError) as error:
        errors.append('malformed_gate:'+type(error).__name__)
    return errors
