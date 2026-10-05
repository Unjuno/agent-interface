import unittest
from doom_source_refresh_v1 import refresh_source, SourceRefreshRefused

def observation(sequence, identifier=None, health='unknown', ammo='unknown'):
    return {'event':'observation', 'sequence':sequence, 'capture_ns':sequence*100,
            'pointer_binding':{'focus':1,'surface':1,'geometry':[0,0,640,480]},
            'id':identifier, 'health':health, 'ammo':ammo}

class Reader:
    def __init__(self, signal): self.signal=signal
    def read(self, row):
        value=row[self.signal]
        return {'status':'unknown' if value == 'unknown' else 'observed', 'value':None if value == 'unknown' else value}

class Harness:
    def __init__(self, images, release=True, reject=False, release_token='lease'):
        self.images=list(images); self.release=release; self.reject=reject; self.commands=[]; self.events=[]; self.release_token=release_token
    def send(self, command):
        self.commands.append(command); identifier=command['id']
        self.events.append({'event':'rejected' if self.reject else 'accepted','id':identifier,'intent_token':'lease'})
        row=dict(self.images.pop(0)); row['id']=identifier if row['id'] is None else row['id']
        self.events.extend([row, {'event':'terminal','id':identifier,'status':'completed',
          'release':{'verified':self.release,'keys_down':[],'buttons_down':[],'intent_token':self.release_token}}])
    def wait(self, predicate, timeout):
        while self.events:
            row=self.events.pop(0)
            if predicate(row): return row
        raise TimeoutError('no matching event')

class SourceRefreshTests(unittest.TestCase):
    def run_refresh(self, harness, initial=None, **kwargs):
        return refresh_source(initial or observation(1), Reader('health'), Reader('ammo'),
          harness.send, harness.wait, 'source-0', **kwargs)
    def test_unknown_then_observed_uses_only_passive_input_and_fresh_frame(self):
        h=Harness([observation(2),observation(3,health=97,ammo=47)])
        row,receipt=self.run_refresh(h)
        self.assertEqual(row['sequence'],3)
        self.assertEqual(receipt['status'],'recovered')
        self.assertEqual(len(h.commands),2)
        self.assertTrue(all(c['steps']==[{'op':'observe'}] for c in h.commands))
    def test_observed_source_unchanged(self):
        h=Harness([]); initial=observation(1,health=97,ammo=47)
        row,receipt=self.run_refresh(h,initial)
        self.assertEqual(row,initial); self.assertEqual(h.commands,[])
    def test_observed_zero_health_is_terminal_refusal_not_unknown_recovery(self):
        h=Harness([observation(2,health=97,ammo=47)])
        with self.assertRaises(SourceRefreshRefused): self.run_refresh(h,observation(1,health=0,ammo=47))
        self.assertEqual(h.commands,[])
    def test_invalid_observed_numbers_refuse_before_submission(self):
        for health,ammo in [(-1,47),(97,-1),(True,47),(97,'bad')]:
            with self.subTest(health=health,ammo=ammo):
                h=Harness([observation(2,health=97,ammo=47)])
                with self.assertRaises(SourceRefreshRefused): self.run_refresh(h,observation(1,health=health,ammo=ammo))
                self.assertEqual(h.commands,[])
    def test_values_above_declared_hud_domains_refuse_before_refresh(self):
        for health,ammo in [(201,47),(97,1000)]:
            with self.subTest(health=health,ammo=ammo):
                h=Harness([observation(2,health=97,ammo=47)])
                with self.assertRaises(SourceRefreshRefused):
                    self.run_refresh(h,observation(1,health=health,ammo=ammo))
                self.assertEqual(h.commands,[])
    def test_invalid_observed_refresh_stops_before_later_positive_frame(self):
        for health,ammo in [(0,47),(97,-1),(97,'bad')]:
            with self.subTest(health=health,ammo=ammo):
                h=Harness([observation(2,health=health,ammo=ammo),observation(3,health=97,ammo=47)])
                with self.assertRaises(SourceRefreshRefused): self.run_refresh(h)
                self.assertEqual(len(h.commands),1)
    def test_persistent_unknown_refuses_after_cap(self):
        h=Harness([observation(x) for x in range(2,6)])
        with self.assertRaises(SourceRefreshRefused) as ctx: self.run_refresh(h)
        self.assertEqual(len(h.commands),4)
        self.assertEqual(ctx.exception.receipt['status'],'refused')
    def test_rejected_refresh_refuses(self):
        with self.assertRaises(SourceRefreshRefused): self.run_refresh(Harness([observation(2)],reject=True))
    def test_unverified_release_refuses_even_when_number_observed(self):
        with self.assertRaises(SourceRefreshRefused): self.run_refresh(Harness([observation(2,health=97,ammo=47)],release=False))
    def test_wrong_frame_identity_never_recovers(self):
        with self.assertRaises(SourceRefreshRefused): self.run_refresh(Harness([observation(2,'other',97,47)]))
    def test_stale_sequence_refuses(self):
        with self.assertRaises(SourceRefreshRefused): self.run_refresh(Harness([observation(1,health=97,ammo=47)]))
    def test_release_identity_mismatch_refuses(self):
        with self.assertRaises(SourceRefreshRefused): self.run_refresh(Harness([observation(2,health=97,ammo=47)],release_token='other'))
    def test_binding_change_refuses(self):
        row=observation(2,health=97,ammo=47); row['pointer_binding']['surface']=2
        with self.assertRaises(SourceRefreshRefused): self.run_refresh(Harness([row]))
    def test_deadline_expiration_prevents_submission(self):
        times=iter([0,3])
        h=Harness([])
        with self.assertRaises(SourceRefreshRefused): self.run_refresh(h,clock=lambda:next(times))
        self.assertEqual(h.commands,[])

if __name__=='__main__': unittest.main()
