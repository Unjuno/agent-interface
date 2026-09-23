"""Opt-in lossy presentation; the runtime must archive every source event."""
class Presentation:
    def __init__(self):
        self.settle=None
        self.latest=None
        self.last_sent=None
        self.context=None
        self.first_settle=True

    def project(self,record):
        event=record['event']
        if event=='step_started':
            self.settle=(record['id'],record['step']) if record['operation']=='settle' else None
            self.first_settle=True
            return []
        if event in ('step_completed','input_admission'):
            return []
        if event=='observation':
            self.latest=record
            context=(record.get('context'),record.get('input_focus_before'),record.get('input_focus_after'))
            changed=context!=self.context
            self.context=context
            in_settle=self.settle==(record['id'],record['step'])
            if not in_settle or self.first_settle or changed or record.get('focus_samples_match') is False:
                self.first_settle=False
                self.last_sent=record['sequence']
                return [record]
            return []
        if event in ('settle_result','terminal'):
            output=[]
            if self.latest is not None and self.latest['sequence']!=self.last_sent:
                output.append(self.latest);self.last_sent=self.latest['sequence']
            output.append(record)
            return output
        # Unknown/critical event types are forwarded rather than silently lost.
        return [record]
