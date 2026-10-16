"""Saved-only cell gates; no acquisition imports."""
import reference as ref
from evidence import check_trace, check_continuity, check_shared_cpu
from qualification import qualify


def validate_cell(spec, cell):
    so, ca = cell['source'], cell['capture']
    historical = ref.audit_cell(spec, so, ca, cell['lifecycle'])
    ref.join(cell['frames'], ca['frames'], 'typed raw frame journal')
    ref.join(cell['source_waits'], so['wait_traces'], 'typed source wait journal')
    ref.need(len(so['wait_traces']) == 2 * len(so['events']), 'complete source waits')
    ref.need(len(cell['source_journal']) == 2 * len(so['events']), 'complete source journal')
    source_metrics, observer_metrics, snapshots = [], [], []
    previous = previous_end = None
    for i, event in enumerate(so['events']):
        identity = ref.integer(event['id'])
        for j, kind in enumerate(('draw', 'clear')):
            t = so['wait_traces'][2*i+j]
            ref.need(t['kind'] == kind and ref.integer(t['id']) == identity, 'source wait identity')
            due = event['onset_ns'] if kind == 'draw' else event['due_clear_ns']
            ref.need(ref.integer(t['due_ns']) == due, 'source wait deadline')
            start, end = event[kind+'_start_ns'], event[kind+'_end_ns']
            ref.join([t['paint_start_ns'], t['paint_end_ns']], [start, end], 'source paint join')
            ref.join(cell['source_journal'][2*i+j],
                     {'event':kind, 'id':identity, 'start':start, 'end':end}, 'source native journal')
            source_metrics.append({'kind':kind, 'id':identity, **check_trace(t, start, end)})
            if previous is not None:
                check_continuity(previous, t, previous_end)
            previous, previous_end = t, end
            snapshots.extend([t['pre'], t['post']])
    ref.need(len(cell['observer_waits']) == 8, 'complete observer wait journal')
    previous = None
    for i, frame in enumerate(ca['frames']):
        ref.join(cell['observer_waits'][i],
                 {k:frame[k] for k in ('index','due_ns','pre','wait','post')}, 'observer wait join')
        observer_metrics.append({'index':i, **check_trace(frame, frame['start_ns'], frame['native_return_ns'])})
        if previous is not None:
            check_continuity(previous, frame, previous['extracted_ns'])
        previous = frame
        snapshots.extend([frame['pre'], frame['post']])
    check_shared_cpu(snapshots)
    qualified = qualify(so, ca)
    return {**qualified, 'historical':historical,
            'source_events_checked':len(so['events']),
            'source_waits_checked':len(so['wait_traces']), 'captures_checked':8,
            'source_wait_metrics':source_metrics, 'observer_wait_metrics':observer_metrics}
