from __future__ import annotations
import hashlib, json, math
import numpy as np

INPUT_DIM = 32
CONFIDENCE_THRESHOLD = np.float32(0.75)
HEADS = (
    [(f'bool_{i:02d}', tuple(f'B{i:02d}_{j}' for j in range(2))) for i in range(16)] +
    [(f'score_{i:02d}', tuple(f'S{i:02d}_{j}' for j in range(5))) for i in range(8)] +
    [(f'choice_{i:02d}', tuple(f'C{i:02d}_{j:02d}' for j in range(16))) for i in range(8)] +
    [('choice_255', tuple(f'H_{j:03d}' for j in range(255)))]
)
TOTAL_LOGITS = sum(len(v) for _, v in HEADS)
assert TOTAL_LOGITS == 455

class CompiledTypedDecisionKernel:
    def __init__(self, parameter_count: int, seed: int):
        if parameter_count < INPUT_DIM + TOTAL_LOGITS:
            raise ValueError('parameter_count_too_small')
        self.parameter_count = int(parameter_count)
        self.seed = int(seed)
        denom = INPUT_DIM + TOTAL_LOGITS
        self.hidden_dim = self.parameter_count // denom
        used = self.hidden_dim * denom
        self.tail_count = self.parameter_count - used
        rng = np.random.default_rng(self.seed)
        self.w1 = rng.standard_normal((self.hidden_dim, INPUT_DIM), dtype=np.float32)
        self.w1 *= np.float32(1.0 / math.sqrt(INPUT_DIM))
        self.w2 = rng.standard_normal((TOTAL_LOGITS, self.hidden_dim), dtype=np.float32)
        self.w2 *= np.float32(1.0 / math.sqrt(self.hidden_dim))
        self.tail = rng.standard_normal((self.tail_count,), dtype=np.float32) if self.tail_count else np.empty((0,), dtype=np.float32)
        exact = self.w1.size + self.w2.size + self.tail.size
        if exact != self.parameter_count:
            raise AssertionError((exact, self.parameter_count))
        self.parameter_bytes = exact * np.dtype(np.float32).itemsize

    def _logits(self, state: np.ndarray) -> np.ndarray:
        x = np.asarray(state, dtype=np.float32)
        if x.shape != (INPUT_DIM,):
            raise ValueError('state_shape')
        hidden = np.tanh(self.w1 @ x)
        logits = self.w2 @ hidden
        if self.tail_count:
            idx = np.arange(self.tail_count, dtype=np.int32) % INPUT_DIM
            tail_feature = x[idx]
            tail_scalar = np.dot(self.tail, tail_feature) / np.float32(max(1, self.tail_count))
            logits[0] += np.float32(1e-4) * tail_scalar
        return logits.astype(np.float32, copy=False)

    def decide(self, state: np.ndarray) -> dict:
        logits = self._logits(state)
        cursor = 0
        outputs = []
        yield_count = 0
        for head_id, vocab in HEADS:
            n = len(vocab)
            z = logits[cursor:cursor+n]
            cursor += n
            m = np.max(z)
            e = np.exp(z - m).astype(np.float32, copy=False)
            probs = e / np.sum(e, dtype=np.float32)
            j = int(np.argmax(probs))
            p = float(probs[j])
            if p < float(CONFIDENCE_THRESHOLD):
                selected = 'YIELD'
                yield_count += 1
            else:
                selected = vocab[j]
            outputs.append({'head_id': head_id, 'selected': selected, 'max_probability': p, 'vocab_size': n})
        if cursor != TOTAL_LOGITS:
            raise AssertionError('logit_cursor')
        return {'outputs': outputs, 'yield_count': yield_count}


def canonical_output_hash(result: dict) -> str:
    payload = json.dumps(result, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(payload).hexdigest()


def validate_typed_output(result: dict) -> list[str]:
    errors = []
    if len(result.get('outputs', [])) != len(HEADS):
        errors.append('head_count')
        return errors
    expected = {k: set(v) | {'YIELD'} for k, v in HEADS}
    for row in result['outputs']:
        hid = row.get('head_id')
        if hid not in expected:
            errors.append('unknown_head')
            continue
        if row.get('selected') not in expected[hid]:
            errors.append('vocab_escape:' + hid)
        p = row.get('max_probability')
        if not isinstance(p, (int, float)) or not math.isfinite(float(p)) or not (0.0 <= float(p) <= 1.0):
            errors.append('probability:' + hid)
    if result.get('yield_count') != sum(r['selected'] == 'YIELD' for r in result['outputs']):
        errors.append('yield_count')
    return errors
