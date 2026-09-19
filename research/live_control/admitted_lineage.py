"""Bind immutable receive metadata only when the executor emits acceptance."""
import copy,threading


class AdmittedLineage:
    def __init__(self):self.pending=None;self.accepted={};self.lock=threading.Lock()
    def begin(self,identifier,metadata):
        with self.lock:
            if self.pending is not None:raise ValueError('pending admission context exists')
            self.pending=(identifier,copy.deepcopy(metadata))
    def end(self):
        with self.lock:self.pending=None
    def attach(self,record):
        name=record.get('event')
        if name not in ('accepted','terminal','effect_evidence','independent_evaluation'):return record
        identifier=record.get('final_program') if name in ('effect_evidence','independent_evaluation') else record.get('id')
        with self.lock:
            if name=='accepted':
                if self.pending is None or self.pending[0]!=identifier:raise ValueError('acceptance lacks matching receive context')
                if identifier in self.accepted:raise ValueError('accepted identity already bound')
                self.accepted[identifier]=copy.deepcopy(self.pending[1])
            metadata=self.accepted.get(identifier)
            if metadata is None:return record
            return dict(record,admitted_request=copy.deepcopy(metadata))
