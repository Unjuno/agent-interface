"""Reconstruct the complete candidate module from exact source and readable delta."""
import hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OLD='''    def key_chord(self, keys: list[str]) -> None:
        for key in keys:
            self.key_state(key, True)
        for key in reversed(keys):
            self.key_state(key, False)
'''
NEW='''    def key_chord(self, keys: list[str]) -> None:
        # Borrow confirmed same-owner holds; do not release them with the chord.
        owned_codes = set(self.held_keycodes.values())
        acquired = [key for key in keys if self._keycode(key) not in owned_codes]
        for key in acquired:
            self.key_state(key, True)
        for key in reversed(acquired):
            self.key_state(key, False)
'''

def main():
    raw=(ROOT/'upstream/backend.py').read_bytes()
    if hashlib.sha256(raw).hexdigest()!='6ba5ea5d4e8fc797fc26a19879cffcfd00926606f53b0ef76fbff5f6b5f779db':
        raise ValueError('wrong upstream source')
    if raw.count(OLD.encode())!=1:raise ValueError('ambiguous patch location')
    result=raw.replace(OLD.encode(),NEW.encode())
    if hashlib.sha256(result).hexdigest()!='3d4e997067823244c4cdd6124e220813e88196a14aa0280a710e881638032a79':
        raise ValueError('wrong candidate identity')
    target=ROOT/'candidate/backend.py'
    if target.exists():
        if target.read_bytes()!=result:raise ValueError('refuse overwrite of different candidate')
    else:
        target.parent.mkdir(exist_ok=True)
        with target.open('xb') as stream:stream.write(result)
    print('complete candidate source verified; no native execution')

if __name__=='__main__':main()
