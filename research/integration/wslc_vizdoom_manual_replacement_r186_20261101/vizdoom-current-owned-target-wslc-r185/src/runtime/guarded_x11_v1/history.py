"""Session-local observations with a bounded decoded-image cache.

Old pixels are reloaded only from their recorded artifact, never recaptured.
Metadata and artifacts still grow with session length; this is not a total
session memory or disk quota. Caller-held image references are not evicted.
"""
from collections import OrderedDict
from collections.abc import MutableMapping
import hashlib
import io
from pathlib import Path

from PIL import Image


class ObservationHistory(MutableMapping):
    def __init__(self, capacity=2):
        if type(capacity) is not int or capacity < 1:
            raise ValueError('positive decoded-image capacity required')
        self.capacity = capacity
        self._records = {}
        self._decoded = OrderedDict()

    def __len__(self):
        return len(self._records)

    def __iter__(self):
        return iter(self._records)

    def _cache(self, key, image):
        self._decoded[key] = image
        self._decoded.move_to_end(key)
        while len(self._decoded) > self.capacity:
            # Do not close an image that another caller may still be using.
            self._decoded.popitem(last=False)

    def __setitem__(self, key, value):
        observation, image = value
        native = observation['native']
        artifact = native['artifact']
        if (image.mode != 'RGB' or image.size != (native['width'], native['height'])
                or artifact['source_raw_sha256'] != native['sha256']):
            raise ValueError('observation image identity mismatch')
        # Pin reload identity independently of mutable returned metadata.
        identity = (artifact['path'], artifact['sha256'], image.size)
        self._records[key] = (observation, identity)
        self._cache(key, image)

    def __getitem__(self, key):
        observation, (path, digest, size) = self._records[key]
        if key in self._decoded:
            image = self._decoded[key]
            self._decoded.move_to_end(key)
        else:
            data = Path(path).read_bytes()
            if hashlib.sha256(data).hexdigest() != digest:
                raise ValueError('retained observation artifact identity mismatch')
            with Image.open(io.BytesIO(data)) as opened:
                if opened.size != size:
                    raise ValueError('retained observation dimensions mismatch')
                image = opened.convert('RGB')
            self._cache(key, image)
        return observation, image

    def __delitem__(self, key):
        del self._records[key]
        self._decoded.pop(key, None)

    def clear(self):
        # MutableMapping.clear would load old images through popitem().
        self._records.clear()
        self._decoded.clear()
