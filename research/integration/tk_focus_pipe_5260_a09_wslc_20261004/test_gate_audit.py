import copy
import unittest
from gate_audit import gate_errors
from test_pipe_audit import packet


def admitted():
    row=packet();value=copy.deepcopy(row['pipe']['frames'][0]['value'])
    row['mode']='PIPE_ACK_TARGET'
    row['injection']={'click_widget':'target','click_started_ns':95,'click_sync_returned_ns':98,
        'gate':{'status':'ADMITTED','ack':value,'state':value,'started_ns':99,
            'decided_ns':106,'deadline_ns':500_000_099,'reason':'CURRENT_TARGET_RECEIPT',
            'samples':[{'checked_ns':106,'state':value,'seen_ns':105,'errors':[],'read_attempts':1}]},
        'key_requests':[{'request_started_ns':107}], 'save_requests':[{'request_started_ns':120}]}
    return row


FIXTURE={'ack_timeout_ms':500,'ack_poll_ms':1,'ack_max_age_ms':50}


class GateAuditTests(unittest.TestCase):
    def test_literal_current_admission_accepts(self):
        self.assertEqual(gate_errors(admitted(),FIXTURE,'a'*64),[])

    def test_changed_admission_fields_refused(self):
        mutations=[lambda r:r['injection']['gate']['samples'].clear(),
            lambda r:r['injection']['gate'].update(decided_ns=97),
            lambda r:r['injection']['gate']['samples'][0].update(read_attempts=0),
            lambda r:r['injection']['gate']['samples'][0].update(seen_ns=104),
            lambda r:r['injection']['gate']['samples'][0].update(errors=['no_frame']),
            lambda r:r['injection']['gate']['ack'].update(sequence=True),
            lambda r:r['injection']['key_requests'][0].update(request_started_ns=105),
            lambda r:r['injection'].update(click_widget='decoy'),
            lambda r:r['injection']['gate'].update(deadline_ns=100),
            lambda r:r['injection']['gate'].update(reason='TIMEOUT')]
        for index,mutation in enumerate(mutations):
            row=admitted();mutation(row)
            with self.subTest(index=index):self.assertTrue(gate_errors(row,FIXTURE,'a'*64))

    def test_refusal_with_key_request_rejected(self):
        row=admitted();row['injection']['gate'].update(status='REFUSED',ack=None,reason='TIMEOUT')
        self.assertTrue(gate_errors(row,FIXTURE,'a'*64))


if __name__=='__main__':unittest.main()
