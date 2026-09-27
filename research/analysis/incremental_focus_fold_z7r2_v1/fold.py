"""Research-only incremental projection of the retained key-state contract.

Single trusted owner, fixed context, append-only contiguous event batches.
No checkpoint loading, native I/O, action, or permission is provided.
"""
from __future__ import annotations

MAX = 2**63-1
CONTEXT_FIELDS = {'epoch','expected_epoch','window','keycode','seed_keymap',
                  'seed_focused','first_ordinal','coverage_complete'}

def integer(value, lower=0, upper=MAX):
    return type(value) is int and lower <= value <= upper

def bitmap(value):
    if type(value) is not str or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
        raise ValueError('invalid bitmap')
    return bytes.fromhex(value)

class Fold:
    """No input event or caller-owned container is retained by this state object."""
    __slots__ = ('mode','window','keycode','next_ordinal','down','known',
                 'focused','pending','poisoned','visited')

    def __init__(self, context, mode='FOCUS_KEYMAP'):
        self.mode=mode; self.window=0; self.keycode=8; self.next_ordinal=0
        self.down=False; self.known=True; self.focused=True; self.pending=False
        self.poisoned=True; self.visited=0
        if type(context) is not dict or set(context) != CONTEXT_FIELDS or mode not in ('FOCUS_KEYMAP','KEY_EDGES'):
            return
        if type(context['epoch']) is not str or not context['epoch'] or context['epoch'] != context['expected_epoch']:
            return
        if not integer(context['window'],1) or not integer(context['keycode'],8,255) or not integer(context['first_ordinal']):
            return
        if context['seed_focused'] is not True or context['coverage_complete'] is not True:
            return
        try: seed=bitmap(context['seed_keymap'])
        except ValueError: return
        self.window=context['window']; self.keycode=context['keycode']
        self.next_ordinal=context['first_ordinal']
        self.down=bool(seed[self.keycode//8] & (1 << (self.keycode%8)))
        self.poisoned=False

    def extend(self, events):
        if self.poisoned: return self.result()
        if type(events) is not list:
            self.poisoned=True
            return self.result()
        for event in events:
            self.visited += 1
            if not self._step(event):
                self.poisoned=True
                break
            self.next_ordinal += 1
        return self.result()

    def _step(self, event):
        if type(event) is not dict or not integer(event.get('ordinal')) or event['ordinal'] != self.next_ordinal:
            return False
        if event.get('send_event') is not False or not integer(event.get('type')):
            return False
        kind=event['type']
        if kind in (2,3):
            if not integer(event.get('window'),1) or event['window'] != self.window or not integer(event.get('keycode'),8,255):
                return False
            if self.mode == 'FOCUS_KEYMAP' and self.pending:
                self.known=False; self.pending=False
            if event['keycode'] == self.keycode: self.down=(kind==2)
        elif kind in (9,10):
            if not integer(event.get('window'),1) or event['window'] != self.window or not integer(event.get('mode'),0,3) or not integer(event.get('detail'),0,7):
                return False
            if self.mode == 'FOCUS_KEYMAP':
                self.known=False
                self.focused=(kind==9 and event['mode']==0)
                self.pending=self.focused
        elif kind == 11:
            try: value=bitmap(event.get('keymap'))
            except ValueError: return False
            if self.mode == 'FOCUS_KEYMAP':
                if not self.pending or not self.focused: return False
                self.down=bool(value[self.keycode//8] & (1 << (self.keycode%8)))
                self.known=True; self.pending=False
        else:
            return False
        return True

    def result(self):
        unresolved=self.poisoned or (self.mode=='FOCUS_KEYMAP' and (not self.known or not self.focused or self.pending))
        return {'status':'UNKNOWN' if unresolved else ('WAIT' if self.down else 'TYPE'),
                'shift_down':None if unresolved else self.down,
                'authority':'none','input_dispatched':False}