"""Opt-in local-servo review projection; full source journal remains mandatory."""
from presentation_v2 import Presentation as Previous

class Presentation(Previous):
    def __init__(self):
        super().__init__();self.local_ids=set()
    def project(self,record):
        kind=record['event'];identifier=record.get('id')
        if kind=='step_started' and record.get('operation')=='pointer_servo':self.local_ids.add(identifier)
        local=identifier in self.local_ids
        previous_context=self.context
        output=super().project(record)
        if kind=='terminal':
            self.local_ids.discard(identifier)
            # The terminal receipt carries the latest historical image reference.
            return [r for r in output if r['event']!='observation'] if local else output
        if not local:return output
        if kind=='observation':
            context=(record.get('context'),record.get('input_focus_before'),record.get('input_focus_after'))
            # Preserve context transitions even if they were detected only in a frame.
            if context!=previous_context or record.get('focus_samples_match') is False:return output
            return []
        if kind in ('pointer_yield','pointer_admission'):return []
        if kind=='servo_feedback' and record.get('reason')=='correct':return []
        # Loss, ambiguity, goal, cancellation, terminal and unknown events pass through.
        return output
