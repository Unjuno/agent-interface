"""Terminal review receipt over the existing event projection; no new authority."""
from presentation import Presentation as Previous

class Presentation(Previous):
    def __init__(self):
        super().__init__();self.outcomes={}
    def project(self,record):
        if record['event']=='servo_outcome':self.outcomes[record['id']]=dict(record)
        output=super().project(record)
        if record['event']!='terminal':return output
        latest=self.latest
        receipt={'runtime_ns':record['terminal_ns'],
                 'clock_scope':'terminal creation time; not current time at delivery',
                 'observation':None,
                 'local_outcome':self.outcomes.pop(record['id'],None),
                 'semantic_verification':'not implied by execution or local visual goal'}
        if latest is not None:
            receipt['observation']={key:latest.get(key) for key in ('sequence','capture_ns','image','image_reused')}
            receipt['observation'].update(program_id=latest.get('id'),
                                           from_this_program=latest.get('id')==record['id'],
                                           freshness='historical; acquire new observation if required')
        return [dict(item,review=receipt) if item is record else item for item in output]
