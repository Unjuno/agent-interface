"""Independent A11 phase evidence audit. No candidate/observer/input imports."""
def phase_errors(row,fixture,freeze_sha):
    errors=[]
    try:
        inj=row['injection'];gate=inj['gate'];ack=gate['ack'];phase=inj['post_admission']
        mode=row['mode'];geometry=row['ready']['geometry'];events=row['app']['events']
        dispatch=phase['dispatch'];ds=phase['dispatch_started_ns'];de=phase['dispatch_completed_ns']
        if mode not in ('STABLE','DRIFT_STALE_CONTROL','DRIFT_REFUSE'):return ['arm']
        if gate['status']!='ADMITTED':errors.append('initial_not_admitted')
        if any(type(v) is not int or v<=0 for v in (gate['decided_ns'],ds,de,ack['sequence'])):
            return errors+['phase_types']
        if not gate['decided_ns']<=ds<=de:errors.append('phase_clock')
        if mode=='STABLE':
            if phase['intervention'] is not None or phase['drift'] is not None:
                errors.append('stable_intervention')
        else:
            intervention=phase['intervention'];observed=phase['drift']
            start=observed['started_ns'];end=observed['decided_ns']
            clocks=[gate['decided_ns'],intervention['started_ns'],intervention['completed_ns'],start,end,ds,de]
            if any(type(t) is not int or t<=0 for t in clocks) or clocks!=sorted(clocks):
                errors.append('phase_clock')
            if (intervention['widget']!='decoy' or any(type(intervention[k]) is not int for k in ('x','y')) or
                intervention['x']!=geometry['decoy_root_x']+geometry['decoy_width']//2 or
                intervention['y']!=geometry['decoy_root_y']+geometry['decoy_height']//2):
                errors.append('intervention_geometry')
            if (observed['status']!='OBSERVED_DRIFT' or observed['reason']!='BOUND_TARGET_OUT_DECOY_IN' or
                observed['deadline_ns']!=start+fixture['drift_timeout_ms']*1_000_000 or
                end>observed['deadline_ns']):errors.append('observation_status')
            reads=row['pipe']['reads'];samples=observed['samples']
            endings=[i for i,r in enumerate(reads,1) if r['status'] in ('EAGAIN','EOF') and
                     start<=r['started_ns']<=r['completed_ns']<=end]
            counts=[s['read_attempts'] for s in samples]
            if (not samples or not endings or any(type(c) is not int for c in counts) or
                counts!=endings):errors.append('poll_custody')
            else:
                previous=start
                for i,sample in enumerate(samples):
                    count=sample['read_attempts'];checked=sample['checked_ns']
                    if (type(checked) is not int or not previous<=reads[count-1]['completed_ns']<=checked<=end or
                        i+1<len(samples) and checked>reads[count]['started_ns']):
                        errors.append('poll_clock')
                    available=[f['value'] for f in row['pipe']['frames']
                        if f['seen_ns']<=reads[count-1]['completed_ns'] and
                        (type(f['value'].get('sequence')) is not int or f['value']['sequence']>ack['sequence'])]
                    if sample['frames']!=available:errors.append('poll_frame_binding')
                    wanted=[]
                    if len(available)!=2:wanted=['transition_count']
                    else:
                        a,b=available
                        if any(f.get('schema')!='issue5260-a09-focus-pipe-v1' or
                            f.get('token')!=row['token'] or f.get('pid')!=row['app_pid'] or
                            f.get('target_id')!=geometry['target_id'] or f.get('freeze_sha256')!=freeze_sha
                            for f in available):wanted.append('binding')
                        if any(type(f.get(k)) is not int or f[k]<=0 for f in available
                               for k in ('pid','target_id','sequence','event_ns','written_ns')):
                            wanted.append('types')
                        else:
                            if ((a.get('kind'),a.get('widget'),a.get('focus_get'))!=('FocusOut','target','other') or
                                (b.get('kind'),b.get('widget'),b.get('focus_get'))!=('FocusIn','decoy','other')):
                                wanted.append('transition_kind')
                            if not (ack['sequence']<a['sequence']<b['sequence'] and
                                intervention['started_ns']<=a['event_ns']<=a['written_ns']<=b['event_ns']<=
                                b['written_ns']<=checked):wanted.append('drift_order')
                        if not wanted and checked-b['written_ns']>fixture['ack_max_age_ms']*1_000_000:
                            wanted=['drift_expired']
                    if sample['errors']!=wanted:errors.append('poll_error_binding')
                    previous=checked
                if (samples[-1]['checked_ns']!=end or samples[-1]['errors'] or
                    observed['frames']!=samples[-1]['frames']):errors.append('decision_binding')
            for frame in observed['frames']:
                matching=[e for e in events if e.get('sequence')==frame['sequence'] and
                          e.get('kind')==frame['kind'] and e.get('widget')==frame['widget'] and
                          e.get('monotonic_ns')==frame['event_ns']]
                if len(matching)!=1:errors.append('app_drift_binding')
        if mode=='DRIFT_REFUSE':
            if dispatch!={'status':'REFUSED','reason':'OBSERVED_DRIFT'}:errors.append('dispatch_status')
            if (inj['key_requests'] or inj['save_requests'] or
                any(e.get('kind') in ('KeyPress','Save') for e in events)):errors.append('refused_emission')
        else:
            if dispatch!={'status':'EMITTED','reason':mode}:errors.append('dispatch_status')
            if any(type(k.get('request_started_ns')) is not int or
                   not ds<=k['request_started_ns']<=k['sync_returned_ns']<=de for k in inj['key_requests']):
                errors.append('key_phase')
    except (KeyError,TypeError,ValueError,IndexError,AttributeError) as e:
        errors.append('malformed_phase:'+type(e).__name__)
    return errors
