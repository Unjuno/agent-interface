"""Independent A09 actual input/effect and load-window custody."""
import json


def effect_errors(row,fixture):
    errors=[]
    try:
        app=row['app'];injection=row['injection'];g=row['ready']['geometry']
        widget=injection['click_widget']
        if (widget not in ('target','decoy') or type(injection['x']) is not int or type(injection['y']) is not int or
                injection['x']!=g[widget+'_root_x']+g[widget+'_width']//2 or
                injection['y']!=g[widget+'_root_y']+g[widget+'_height']//2):errors.append('click_geometry')
        keys=injection['key_requests'];saves=injection['save_requests']
        events=app['events'];key_events=[event for event in events if event['kind']=='KeyPress']
        save_events=[event for event in events if event['kind']=='Save']
        if injection['gate']['status']=='REFUSED':
            if (keys or saves or key_events or save_events or type(app['save_count']) is not int or
                    app['save_count']!=0 or app['saved_text'] is not None or
                    app['final_target']!='' or app['final_decoy']!='' or
                    any(name in app for name in ('first_key_ns','first_key_widget','first_visual'))):
                errors.append('refusal_effect')
            return errors
        if len(keys)!=3 or len(saves)!=1 or len(key_events)!=3 or len(save_events)!=1:
            return errors+['input_count']
        if ''.join(event['char'] for event in key_events)!=fixture['payload']:
            errors.append('key_events')
        for index,(key,event) in enumerate(zip(keys,key_events)):
            if (any(type(key.get(name)) is not int for name in ('index','keycode','request_started_ns','sync_returned_ns')) or
                    key['index']!=index or key['char']!=fixture['payload'][index] or key['keycode']<=0 or
                    not injection['gate']['decided_ns']<=key['request_started_ns']<=key['sync_returned_ns'] or
                    event['widget'] not in ('target','decoy') or event['monotonic_ns']<key['request_started_ns']):
                errors.append('key_receipt')
            if index and key['request_started_ns']<keys[index-1]['sync_returned_ns']+fixture['inter_key_gap_ms']*1_000_000:
                errors.append('key_gap')
        save=saves[0]
        if (save['x']!=g['save_root_x']+g['save_width']//2 or save['y']!=g['save_root_y']+g['save_height']//2 or
                not keys[-1]['sync_returned_ns']+fixture['save_delay_after_last_key_ms']*1_000_000
                <=save['request_started_ns']<=save['sync_returned_ns']<=app['ended_ns'] or
                type(app['save_count']) is not int or app['save_count']!=1 or
                save_events[0]['monotonic_ns']<save['request_started_ns']):errors.append('save_receipt')
        if (app['first_key_widget']!=key_events[0]['widget'] or
                not key_events[0]['monotonic_ns']<=app['first_key_ns']<=app['ended_ns']):errors.append('first_key')
        target=''.join(event['char'] for event in key_events if event['widget']=='target')
        decoy=''.join(event['char'] for event in key_events if event['widget']=='decoy')
        if app['final_target']!=target or app['final_decoy']!=decoy or app['saved_text']!=target:
            errors.append('effect_binding')
    except (KeyError,TypeError,ValueError,IndexError) as error:
        errors.append('malformed_effect:'+type(error).__name__)
    return errors

def worker_errors(row,fixture):
    try:
        worker=row['worker']
        if row['load']=='idle':return [] if worker=={'pid':None,'exit':None} else ['idle_worker']
        if row['load']!='cpu_busy':return ['unknown_load']
        if any(type(worker.get(name)) is not int or worker[name]<=0 for name in ('pid','start_ns','end_ns')):
            return ['worker_types']
        start,end=worker['start_ns'],worker['end_ns'];injection=row['injection']
        phase_end=(injection['key_requests'][0]['sync_returned_ns'] if injection['gate']['status']=='ADMITTED'
                   else injection['gate']['decided_ns'])
        if (type(worker['exit']) is not int or worker['exit']!=0 or worker['stderr']!='' or
                json.loads(worker['stdout'])!={'start_ns':start,'end_ns':end} or
                end-start<fixture['busy_worker_duration_ms']*1_000_000):return ['worker_receipt']
        if not start<=injection['click_started_ns']<=phase_end<=end:return ['worker_phase_not_covered']
        return []
    except (KeyError,TypeError,ValueError,IndexError):return ['malformed_worker']
