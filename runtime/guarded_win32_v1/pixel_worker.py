"""Pure declared RGB predicate; no native session, input or subprocess creation."""
import sys, json, base64, hashlib

def evaluate_samples(request):
    width, height = request['size']
    samples = request['samples']
    conditions = request['conditions']
    if type(width) is not int or type(height) is not int or min(width, height) < 1:
        raise ValueError('invalid image size')
    if type(conditions) is not list or not 1 <= len(conditions) <= 64 or type(samples) is not list or (len(samples) != len(conditions)):
        raise ValueError('invalid sample count')
    encoded = json.dumps(samples, separators=(',', ':'), sort_keys=True).encode()
    if hashlib.sha256(encoded).hexdigest() != request['context']['sample_sha256']:
        raise ValueError('sample digest mismatch')
    success = True
    for condition, sample in zip(conditions, samples):
        x, y = condition['point']
        if type(x) is not int or type(y) is not int or (not (0 <= x < width and 0 <= y < height)) or (sample['point'] != [x, y]):
            raise ValueError('sample coordinate mismatch')
        for rgb in [condition['rgb'], sample['rgb']]:
            if type(rgb) is not list or len(rgb) != 3 or any((type(v) is not int or not 0 <= v <= 255 for v in rgb)):
                raise ValueError('invalid RGB')
        success = success and sample['rgb'] == condition['rgb']
    return {'context': request['context'], 'task_success': success}

def evaluate(request):
    if 'samples' in request:
        return evaluate_samples(request)
    width, height = request['size']
    raw = base64.b64decode(request['rgb'], validate=True)
    if type(width) is not int or type(height) is not int or min(width, height) < 1 or (len(raw) != width * height * 3):
        raise ValueError('invalid image')
    if hashlib.sha256(raw).hexdigest() != request['context']['rgb_sha256']:
        raise ValueError('image digest mismatch')
    conditions = request['conditions']
    if type(conditions) is not list or not 1 <= len(conditions) <= 64:
        raise ValueError('bounded explicit conditions required')
    success = True
    for condition in conditions:
        x, y = condition['point']
        rgb = condition['rgb']
        if type(x) is not int or type(y) is not int or (not (0 <= x < width and 0 <= y < height)):
            raise ValueError('point outside image')
        if type(rgb) is not list or len(rgb) != 3 or any((type(v) is not int or not 0 <= v <= 255 for v in rgb)):
            raise ValueError('invalid RGB condition')
        offset = (y * width + x) * 3
        success = success and list(raw[offset:offset + 3]) == rgb
    return {'context': request['context'], 'task_success': success}
if __name__ == '__main__':
    request = json.loads(sys.stdin.buffer.read(1048577))
    print(json.dumps(evaluate(request)))
