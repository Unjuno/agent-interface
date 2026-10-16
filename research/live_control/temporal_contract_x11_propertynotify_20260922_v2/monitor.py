from __future__ import annotations

PENDING='PENDING'
SATISFIED='SATISFIED'
VIOLATED='VIOLATED'
EXPIRED='EXPIRED'
UNKNOWN='UNKNOWN'
TERMINAL={SATISFIED,VIOLATED,EXPIRED,UNKNOWN}
KINDS={'AB','P','CD','XY'}

class Monitor:
    __slots__=('kind','param','status','current_t','labels','anchor','p_value','p_start')

    def __init__(self,kind:str,param:int|None=None):
        if kind not in KINDS: raise ValueError(kind)
        if kind in {'AB','P','XY'} and (not isinstance(param,int) or param<=0): raise ValueError('param')
        if kind=='CD' and param is not None: raise ValueError('CD has no param')
        self.kind=kind;self.param=param;self.status=PENDING
        self.current_t=None;self.labels=set();self.anchor=None
        self.p_value=None;self.p_start=None

    def state_shape(self):
        return ('kind','param','status','current_t','labels','anchor','p_value','p_start')

    def feed(self,t:int,value):
        if self.status in TERMINAL: return self.status
        if not isinstance(t,int): self.status=UNKNOWN; return self.status
        if self.current_t is not None and t<self.current_t:
            self.status=UNKNOWN; return self.status
        if self.current_t is None:
            self.current_t=t
        elif t>self.current_t:
            self._advance(t)
            if self.status in TERMINAL: return self.status
            self.current_t=t
            if self.kind!='P': self.labels=set()
        if self.kind=='P':
            if not isinstance(value,bool): self.status=UNKNOWN; return self.status
            self._feed_p(value)
        else:
            try: incoming=set(value)
            except Exception: self.status=UNKNOWN; return self.status
            allowed={'A','B'} if self.kind=='AB' else ({'C','D'} if self.kind=='CD' else {'X','Y'})
            if not incoming<=allowed: self.status=UNKNOWN; return self.status
            self.labels.update(incoming)
            self._after_labels()
        return self.status

    def _advance(self,new_t:int):
        if self.kind=='AB':
            if self.anchor is not None and new_t>self.anchor+self.param:
                self.status=EXPIRED
        elif self.kind=='P':
            if self.p_value is True and self.p_start is not None and new_t-self.p_start>=self.param:
                self.status=SATISFIED
        elif self.kind=='CD':
            if 'C' in self.labels and 'D' not in self.labels:
                self.status=VIOLATED
        elif self.kind=='XY':
            if self.anchor is not None and new_t>self.anchor+self.param:
                self.status=SATISFIED

    def _after_labels(self):
        t=self.current_t
        if self.kind=='AB':
            if self.anchor is None and 'A' in self.labels:
                self.anchor=t
            if self.anchor is not None and self.anchor<=t<=self.anchor+self.param and 'B' in self.labels:
                self.status=SATISFIED
        elif self.kind=='CD':
            if 'D' in self.labels:
                self.status=SATISFIED
        elif self.kind=='XY':
            if self.anchor is None and 'X' in self.labels:
                self.anchor=t
            if self.anchor is not None and self.anchor<t<=self.anchor+self.param and 'Y' in self.labels:
                self.status=VIOLATED

    def _feed_p(self,value:bool):
        if value:
            if self.p_value is not True:
                self.p_start=self.current_t
            self.p_value=True
        else:
            self.p_value=False
            self.p_start=None
