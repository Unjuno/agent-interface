"""Passive focus recorder; file publication is an explicit treatment."""
import copy
import time


class FocusTrace:
    def __init__(self,mode,write=None,clock=time.monotonic_ns):
        if mode not in ('MEMORY_ONLY','SYNC_FILE'):
            raise ValueError('unknown instrumentation mode')
        if mode=='SYNC_FILE' and not callable(write):
            raise ValueError('SYNC_FILE requires a writer')
        self.mode=mode
        self.write=write
        self.clock=clock
        self.events=[]
        self.publications=[]
        self.callbacks=[]
        self.last_state=None
        self.ack=None

    def _publish(self,name,value,event_sequence):
        started=self.clock()
        result=self.write(name,copy.deepcopy(value))
        self.publications.append({'path':name,'event_sequence':event_sequence,
            'started_ns':started,'completed_ns':self.clock(),
            'writer_trace':copy.deepcopy(result)})

    def record(self,kind,widget,binding):
        if kind not in ('FocusIn','FocusOut') or widget not in ('target','decoy'):
            raise ValueError('unknown focus event')
        event={'kind':kind,'widget':widget,'monotonic_ns':self.clock(),
               'sequence':len(self.events)+1}
        self.events.append(event)
        state={name:copy.deepcopy(binding[name]) for name in ('token','pid','target_id')}
        state.update(widget=widget if kind=='FocusIn' else 'none',
                     sequence=event['sequence'],event_ns=event['monotonic_ns'])
        self.last_state=copy.deepcopy(state)
        first_target=kind=='FocusIn' and widget=='target' and self.ack is None
        if first_target:
            self.ack={**copy.deepcopy(state),'schema':'issue5260-a07-focus-ack-v1',
                      'focus_get':binding.get('focus_get','unknown'),
                      'written_ns':self.clock()}
        if self.mode=='SYNC_FILE':
            self._publish('focus_state.json',state,event['sequence'])
            if first_target:
                self._publish('focus_ack.json',self.ack,event['sequence'])
        self.callbacks.append({'event_sequence':event['sequence'],
            'started_ns':event['monotonic_ns'],'completed_record_ns':self.clock()})
        return copy.deepcopy(event)

    def snapshot(self):
        return copy.deepcopy({'mode':self.mode,'events':self.events,
                              'publications':self.publications,
                              'callbacks':self.callbacks,
                              'last_state':self.last_state,'ack':self.ack})
