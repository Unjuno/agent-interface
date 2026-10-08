"""Research-only exposure gate. No ACK, recovery, or action authority."""
from upstream.reader import read_pending


def read_epoch_bound(path, *, stream_id, cursor=None, max_records=32):
    """Bind every returned notification to an owner-supplied lifetime.

    The producer must persist a distinct epoch in each record. This checks one
    read snapshot, not producer authenticity or the current state after reading.
    A rejected batch exposes neither a partial record list nor a new cursor.
    """
    receipt = read_pending(path, stream_id=stream_id, cursor=cursor,
                           max_records=max_records)
    if any(type(row.get('producer_epoch')) is not str
           or row['producer_epoch'] != stream_id for row in receipt['records']):
        raise ValueError('PRODUCER_EPOCH_MISMATCH')
    return receipt
