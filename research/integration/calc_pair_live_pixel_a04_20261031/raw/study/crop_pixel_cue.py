"""Exact reviewed pixel cue; no OCR, authority or independent saved score."""
import hashlib
BOXES=((100,145,123,157),(100,162,123,174))

def create_reference(image):
    if getattr(image,'mode',None)!='RGB' or getattr(image,'size',None)!=(1280,800):
        raise ValueError('reviewed RGB frame must have fixed geometry')
    return tuple(hashlib.sha256(image.crop(box).tobytes()).hexdigest() for box in BOXES)

def classify(image,reference):
    if type(reference) is not tuple or len(reference)!=2 or any(type(x) is not str or len(x)!=64 or any(c not in '0123456789abcdef' for c in x) for x in reference):
        return 'unknown'
    try: actual=create_reference(image)
    except (ValueError,TypeError,AttributeError): return 'unknown'
    return 'filled' if actual==reference else 'unknown'
