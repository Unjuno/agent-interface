"""Capture-bound OCR preview gate that arms a reviewed modal guard once.

The caller supplies reviewed static regions, capture ownership and OCR runner;
this module neither finds a dialog nor mints or dispatches input. Runner timeout
is passed to the runner; only a conforming runner provides the bound.
"""
import hashlib
import io
import subprocess
import time
from PIL import Image, ImageOps
from research.live_control.calc_ocr_pair_cue_v1 import classify_pair
from research.live_control.reviewed_modal_guard_v1 import ReviewedModalGuard


class ReviewedPreviewGate:
    def __init__(self, bridge, *, reference, static_regions, preview_regions, title,
                 expected, deadline_ns, max_age_ns=1_500_000_000,
                 runner=subprocess.run, clock=time.monotonic_ns):
        if (type(static_regions) is not tuple or not static_regions or
                type(preview_regions) is not tuple or len(preview_regions) != 2 or not callable(runner)):
            raise ValueError('two reviewed preview regions and OCR runner required')
        classify_pair('', '', expected=expected)
        self.bridge, self.reference = bridge, reference.copy()
        self.static_regions, self.preview_regions = static_regions, preview_regions
        self.title, self.expected, self.deadline_ns = title, expected, deadline_ns
        self.max_age_ns, self.runner, self.clock = max_age_ns, runner, clock
        # Validate all region coordinates and constructor arguments before any OCR.
        self._make_guard(self.reference, static_regions + preview_regions)
        self.used = False
        self.guard = None

    def _make_guard(self, reference, regions):
        return ReviewedModalGuard(self.bridge, reference=reference, regions=regions,
                                  title=self.title, deadline_ns=self.deadline_ns,
                                  max_age_ns=self.max_age_ns, clock=self.clock)

    def arm(self, native, image):
        if self.used:
            raise ValueError('preview gate is single use')
        self.used = True
        records = []
        try:
            # Verify the exact current retained capture against the reviewed static UI.
            self._make_guard(self.reference, self.static_regions).arm(native, image)
            texts = []
            for index, box in enumerate(self.preview_regions):
                now = self.clock()
                remaining_ns = min(self.deadline_ns, native['capture_ns'] + self.max_age_ns) - now
                if type(now) is not int or remaining_ns <= 0:
                    raise TimeoutError('preview budget exhausted')
                timeout = min(1.0, remaining_ns / 1_000_000_000)
                crop = image.crop(box).convert('L').resize(((box[2] - box[0]) * 4,
                                                            (box[3] - box[1]) * 4), Image.Resampling.LANCZOS)
                crop = ImageOps.expand(crop, border=16, fill=255)
                buffer = io.BytesIO()
                crop.save(buffer, format='PNG')
                data = buffer.getvalue()
                command = ['tesseract', 'stdin', 'stdout', '--psm', '7', '-c',
                           'tessedit_char_whitelist=0123456789', 'tsv']
                record = {'index': index, 'box': list(box), 'command': command.copy(),
                          'input_sha256': hashlib.sha256(data).hexdigest(), 'timeout_seconds': timeout}
                records.append(record)
                result = self.runner(command, input=data, capture_output=True, timeout=timeout, check=False)
                if (type(result.returncode) is not int or result.returncode != 0 or
                        type(result.stdout) is not bytes or type(result.stderr) is not bytes or
                        len(result.stdout) > 1024 * 1024 or len(result.stderr) > 1024 * 1024):
                    raise ValueError('invalid OCR result')
                record.update(returncode=result.returncode, stdout_sha256=hashlib.sha256(result.stdout).hexdigest(),
                              stderr_sha256=hashlib.sha256(result.stderr).hexdigest())
                texts.append(result.stdout.decode('utf-8'))
            # A callback may have changed focus, capture sequence or time during OCR.
            self._make_guard(self.reference, self.static_regions).arm(native, image)
            cue = classify_pair(*texts, expected=self.expected)
            if cue != 'filled':
                return {'status': cue, 'attempts': records}
            guard = self._make_guard(image, self.static_regions + self.preview_regions)
            guard.arm(native, image)
            self.guard = guard
            return {'status': 'armed', 'attempts': records}
        except Exception as error:
            return {'status': 'unknown', 'reason': type(error).__name__, 'attempts': records}
