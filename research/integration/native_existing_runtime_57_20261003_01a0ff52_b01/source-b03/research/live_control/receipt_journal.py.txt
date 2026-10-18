"""Single-writer receipt journal with per-record flush and sticky I/O failure."""
import json


class ReceiptJournal:
    def __init__(self, stream):
        self.stream = stream
        self.failed = False
        self.closed = False
        self.confirmed = 0

    def append(self, record):
        if self.failed or self.closed:
            raise RuntimeError('receipt journal unavailable')
        # Serialization failures do not touch the stream.
        data = (json.dumps(record)+'\n').encode('utf-8')
        try:
            written = self.stream.write(data)
            if written != len(data):
                raise OSError('short receipt write')
            self.stream.flush()
        except Exception:
            self.failed = True
            raise
        self.confirmed += 1

    def close(self):
        if not self.closed:
            self.closed = True
            try:
                self.stream.close()
            except Exception:
                self.failed = True
                raise
