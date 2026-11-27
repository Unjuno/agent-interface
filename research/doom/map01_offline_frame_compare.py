"""Compare saved MAP01 frames for research; never authorizes input or scoring."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops, ImageStat

REGIONS = {
    'viewport': (321, 180, 961, 580),
    'ceiling': (440, 190, 850, 325),
    'floor': (321, 465, 961, 530),
    'right_wall': (805, 200, 960, 470),
}


def load(path):
    data = Path(path).read_bytes()
    from io import BytesIO
    with Image.open(BytesIO(data)) as image:
        result = image.convert('RGB')
    if result.size != (1280, 800):
        raise ValueError('expected registered 1280x800 frame')
    return result, hashlib.sha256(data).hexdigest()


def compare(reference, candidate):
    result = {}
    for name, roi in REGIONS.items():
        diff = ImageChops.difference(reference.crop(roi), candidate.crop(roi))
        components = (roi[2] - roi[0]) * (roi[3] - roi[1]) * 3
        result[name] = {'roi': list(roi), 'difference_sum': int(sum(ImageStat.Stat(diff).sum)),
                        'components': components}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference')
    parser.add_argument('candidates', nargs='+')
    args = parser.parse_args()
    reference, reference_sha = load(args.reference)
    rows = []
    for path in args.candidates:
        candidate, digest = load(path)
        rows.append({'path': str(Path(path)), 'sha256': digest,
                     'regions': compare(reference, candidate)})
    print(json.dumps({'schema': 'map01-offline-frame-comparison-v1',
                      'reference': args.reference, 'reference_sha256': reference_sha,
                      'candidates': rows, 'grants_input_authority': False,
                      'scope': 'retrospective pixel differences, not position or task proof'},
                     sort_keys=True, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
