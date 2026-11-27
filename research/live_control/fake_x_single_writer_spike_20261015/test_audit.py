import copy
import unittest
from .audit import audit


def fixture():
    # Hand-derived separated/cancel trace. No producer or runtime imports.
    events = [dict(n=0,event='injected',kind=2,code=1,cleanup=False,thread_id=7),
        dict(n=1,event='injected',kind=4,code=1,cleanup=False,thread_id=7),
        dict(n=2,event='cancel_requested',thread_id=8),
        dict(n=3,event='authority_revoked',epoch=1,thread_id=7),
        dict(n=4,event='cleanup_requested',thread_id=7),
        dict(n=5,event='injected',kind=3,code=1,cleanup=True,thread_id=7),
        dict(n=6,event='injected',kind=5,code=1,cleanup=True,thread_id=7),
        dict(n=7,event='cleanup_returned',receipt={'verified':True,'keys_down':[],'buttons_down':[]},thread_id=7),
        dict(n=8,event='query_returned',proof={'epoch':0},thread_id=9),
        dict(n=9,event='reply_discarded',proof={'epoch':0},current_epoch=1,thread_id=7)]
    neutral = dict(keys=[],buttons=[],receipt={'verified':True,'keys_down':[],'buttons_down':[]},
        revoked=True,epoch=1,owner_alive=False,observation_blocked=False,clock_ns=1,deadline_ns=10)
    events.insert(7, dict(event='keymap_read',keys=[],thread_id=7))
    events.insert(8, dict(event='pointer_read',buttons=[],thread_id=7))
    for n, event in enumerate(events): event['n'] = n
    return dict(arm='separated',mode='cancel',owner_thread_id=7,errors=[],events=events,
        boundary=dict(neutral,owner_alive=True,observation_blocked=True,event_count=10),
        final=neutral,pending_backend_keys={},pending_backend_buttons=[],backend_resumed=None)


class AuditTests(unittest.TestCase):
    def test_hand_derived_valid(self):
        self.assertEqual(audit(fixture()), [])

    def test_mutations_have_specific_refusals(self):
        for mutation, expected in [('held','BOUNDARY_NEUTRAL'), ('writer','SINGLE_WRITER'),
                ('late','NO_LATE_PRESS'), ('verified','CLEANUP_CONFIRMED'),
                ('duplicate','ONE_CLEANUP'), ('resurrect','STALE_REPLY_DISCARDED'),
                ('authority','SNAPSHOT_AUTHORITY'), ('order','REVOKE_BEFORE_CLEANUP'),
                ('readback','FAKE_READBACK_CONFIRMS_EMPTY'),
                ('early_reads','READBACK_MATCHES_EMISSIONS')]:
            row = copy.deepcopy(fixture())
            if mutation == 'held': row['boundary']['keys'] = [1]
            elif mutation == 'writer': row['events'][0]['thread_id'] = 99
            elif mutation == 'late': row['events'][5].update(kind=2,code=2)
            elif mutation == 'verified': next(e for e in row['events'] if e['event']=='cleanup_returned')['receipt']['verified'] = False
            elif mutation == 'duplicate': row['events'].append(dict(n=len(row['events']),event='cleanup_requested',thread_id=7))
            elif mutation == 'resurrect': next(e for e in row['events'] if e['event']=='reply_discarded')['event'] = 'reply_admitted'
            elif mutation == 'authority': row['boundary'].update(revoked=False,epoch=0)
            elif mutation == 'order':
                row['events'][3],row['events'][4] = row['events'][4],row['events'][3]
                for n,event in enumerate(row['events']): event['n']=n
            elif mutation == 'readback': next(e for e in row['events'] if e['event']=='keymap_read')['keys']=[1]
            elif mutation == 'early_reads':
                e = row['events']
                row['events'] = e[:5]+e[7:9]+e[5:7]+e[9:]
                for n,event in enumerate(row['events']): event['n']=n
            with self.subTest(mutation=mutation):
                self.assertIn(expected, audit(row))

    def test_healthy_releases_have_the_backend_order(self):
        row = fixture()
        row.update(mode='healthy')
        row['events'] = [dict(event='injected',kind=kind,code=code,cleanup=cleanup,thread_id=7)
            for kind,code,cleanup in [(2,1,False),(4,1,False)]] + [
            dict(event='query_returned',proof={'epoch':0},thread_id=9),
            dict(event='reply_admitted',proof={'epoch':0},current_epoch=0,thread_id=7)] + [
            dict(event='injected',kind=2,code=2,cleanup=False,thread_id=7),
            dict(event='injected',kind=4,code=3,cleanup=False,thread_id=7),
            dict(event='cleanup_requested',thread_id=7)] + [
            dict(event='injected',kind=kind,code=code,cleanup=True,thread_id=7)
            for kind,code in [(3,1),(3,2),(5,1),(5,3)]] + [
            dict(event='keymap_read',keys=[],thread_id=7),
            dict(event='pointer_read',buttons=[],thread_id=7),
            dict(event='cleanup_returned',receipt={'verified':True,'keys_down':[],'buttons_down':[]},thread_id=7)]
        for n,event in enumerate(row['events']): event['n']=n
        row['boundary'].update(keys=[1],buttons=[1],receipt=None,epoch=0,revoked=False,event_count=2)
        row['final'].update(epoch=0,revoked=False)
        self.assertEqual(audit(row), [])
        releases = [e for e in row['events'] if e['event']=='injected' and e['cleanup']]
        values = [(e['kind'],e['code']) for e in releases][::-1]
        for event,(kind,code) in zip(releases,values): event.update(kind=kind,code=code)
        self.assertIn('HEALTHY_RELEASE_ORDER', audit(row))


if __name__ == '__main__':
    unittest.main()
