"""Research prototype: append-only positive integer keys, shallow values.

Immutable chunks let forks share old entries. This is not ObservationHistory:
it intentionally has no arbitrary overwrite, deletion, image cache or artifact
reload, and cannot replace the public MutableMapping contract.
"""
from bisect import bisect_left


class SegmentedAppendMap:
    def __init__(self, chunk_size=256):
        if type(chunk_size) is not int or chunk_size <= 0:
            raise ValueError('positive chunk size required')
        self.chunk_size=chunk_size
        self._chunks=()
        self._high=()
        self._length=0

    def fork(self):
        copy=SegmentedAppendMap(self.chunk_size)
        copy._chunks=self._chunks
        copy._high=self._high
        copy._length=self._length
        return copy

    def append(self, key, value):
        if type(key) is not int or key <= 0 or (self._high and key <= self._high[-1]):
            raise ValueError('strictly increasing positive integer key required')
        row=(key,value)
        if self._chunks and len(self._chunks[-1]) < self.chunk_size:
            block=self._chunks[-1]+(row,)
            self._chunks=self._chunks[:-1]+(block,)
            self._high=self._high[:-1]+(key,)
        else:
            self._chunks=self._chunks+((row,),)
            self._high=self._high+(key,)
        self._length+=1

    def __getitem__(self,key):
        if type(key) is not int:raise KeyError(key)
        block_index=bisect_left(self._high,key)
        if block_index==len(self._chunks):raise KeyError(key)
        block=self._chunks[block_index]
        row_index=bisect_left(block,(key,))
        if row_index==len(block) or block[row_index][0]!=key:raise KeyError(key)
        return block[row_index][1]

    def __len__(self):return self._length

    def __iter__(self):
        for block in self._chunks:
            for key,_ in block:yield key
