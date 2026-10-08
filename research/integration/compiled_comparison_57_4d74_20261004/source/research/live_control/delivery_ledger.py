"""Record stdout flush endpoints and caller-declared observation provenance."""
import copy
import time


class DeliveryLedger:
    def __init__(self):
        self.records = {}
        self.next_id = 1

    def prepare(self, item):
        result = copy.deepcopy(item)
        result['delivery_id'] = f'delivery:{self.next_id}'
        self.next_id += 1
        return result

    def flushed(self, item, byte_count, started_ns):
        # Flush is an output-stream endpoint, never proof of model receipt/viewing.
        observation = item if item.get('event') == 'observation' else item.get('review', {}).get('observation')
        record = dict(event='delivery_flush', delivery_id=item['delivery_id'],
                      started_ns=started_ns, flushed_ns=time.perf_counter_ns(),
                      utf8_bytes=byte_count, observation=copy.deepcopy(observation))
        self.records[item['delivery_id']] = record
        return record

    def validate(self, evidence):
        if not isinstance(evidence, dict) or set(evidence) != {'delivery_id', 'observation_sequence', 'producer'}:
            raise ValueError('invalid decision_evidence fields')
        if evidence['producer'] not in ('assistant', 'scripted', 'human'):
            raise ValueError('unknown declared producer')
        record = self.records.get(evidence['delivery_id'])
        if record is None:
            raise ValueError('delivery not successfully flushed')
        observation = record['observation']
        if not observation or observation['sequence'] != evidence['observation_sequence']:
            raise ValueError('delivery observation mismatch')
        return dict(event='decision_evidence', **evidence, image=observation['image'],
                    provenance='caller-declared reference; model viewing unverified',
                    authority='none; ordinary admission remains required')
