"""Experimental segmented integer append path with full dict fallback.

No thread safety is added; callers must retain the history's existing
serialization contract. Values are shallow-shared exactly as with dict.copy.
"""
from collections.abc import MutableMapping
from .segmented_append_map import SegmentedAppendMap


class HybridRecords(MutableMapping):
    def __init__(self):
        self._segments=SegmentedAppendMap()
        self._fallback=None

    def _dict(self):
        if self._fallback is None:
            self._fallback={key:value for block in self._segments._chunks for key,value in block}
            self._segments=SegmentedAppendMap()
        return self._fallback

    def copy(self):
        result=HybridRecords()
        if self._fallback is None:result._segments=self._segments.fork()
        else:result._fallback=self._fallback.copy()
        return result

    def __getitem__(self,key):
        if self._fallback is not None:return self._fallback[key]
        if type(key) is not int:return self._dict()[key]
        return self._segments[key]

    def __setitem__(self,key,value):
        if self._fallback is not None:
            self._fallback[key]=value;return
        high=self._segments._high
        if type(key) is int and key>0 and (not high or key>high[-1]):
            self._segments.append(key,value);return
        self._dict()[key]=value

    def __delitem__(self,key):
        del self._dict()[key]

    def __iter__(self):
        return iter(self._dict())

    def __len__(self):
        return len(self._fallback if self._fallback is not None else self._segments)

    def clear(self):
        self._segments=SegmentedAppendMap();self._fallback=None
