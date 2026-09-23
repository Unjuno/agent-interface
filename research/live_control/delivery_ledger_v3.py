"""Candidate bounded observation-reference retention; independent of authority."""
from collections import OrderedDict
import time
from delivery_ledger_v2 import DeliveryLedger as Previous


class DeliveryLedger(Previous):
    def __init__(self, capacity=128):
        if type(capacity) is not int or capacity < 1:
            raise ValueError('positive integer capacity required')
        super().__init__()
        self.capacity = capacity
        self.records = OrderedDict()

    def flushed(self, item, byte_count, started_ns):
        source = item if item.get('event') == 'observation' else item.get('review', {}).get('observation')
        observation = None if not source else {
            key: source[key] for key in ('sequence', 'image', 'capture_ns', 'image_reused') if key in source}
        record = dict(event='delivery_flush', delivery_id=item['delivery_id'],
                      started_ns=started_ns, flushed_ns=time.perf_counter_ns(),
                      utf8_bytes=byte_count, observation=observation)
        if observation is not None:
            self.records[item['delivery_id']] = record
            while len(self.records) > self.capacity:
                self.records.popitem(last=False)
        return record
