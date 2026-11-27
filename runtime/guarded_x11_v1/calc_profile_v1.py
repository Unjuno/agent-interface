"""One fixed Calc compiled profile with a trusted OCR input dependency.

This is scoped to the retained 731/864, 1280x800 LibreOffice Calc task. It is
not a general OCR service and does not score saved-workbook completion. OCR
uses one bounded, upscaled two-cell crop from each already-guarded frame.
"""
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
import math
import re
import shutil
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageOps

PROFILE_ID = 'calc-ocr-save-v1'
_WIDTH, _HEIGHT = 1280, 800
_CELL_BOXES = {'A1': (36, 143, 126, 159), 'A2': (36, 160, 126, 177)}
# Calc opens with A1 focused. The menu text is a stable observation-only target
# for keyboard input, so editing A1/A2 cannot invalidate the reference.
_ENTRY_ANCHOR = {'point': [16, 31], 'box': [4, 23, 24, 16],
                 'offset': [12, 8]}
_EXPECTED = {'A1': '731', 'A2': '864'}
_MAX_AGE_NS = 1_500_000_000
_MAX_RUNTIME_NS = 10_000_000_000
_MAX_OCR_BYTES = 32 * 1024 * 1024
_TSV_HEADER = ('level', 'left', 'top', 'width', 'height', 'conf', 'text')
_ODS_NS = {'table':'urn:oasis:names:tc:opendocument:xmlns:table:1.0',
           'office':'urn:oasis:names:tc:opendocument:xmlns:office:1.0',
           'text':'urn:oasis:names:tc:opendocument:xmlns:text:1.0'}


class _UnscorableArtifact(ValueError):
    """Well-formed Flat ODF whose structure exceeds this fixed scorer."""


def validate_calc_task_values(values=None):
    """Return exactly two bounded decimal cell values for the registered task."""
    if values is None:
        values = _EXPECTED
    if (type(values) is not dict or set(values) != set(_EXPECTED)
            or any(type(value) is not str
                   or not re.fullmatch(r'(?:0|[1-9][0-9]{0,8})', value)
                   for value in values.values())):
        raise ValueError('Calc task requires bounded decimal A1 and A2 values')
    return dict(values)


def verify_saved_fods(path, *, expected=None):
    """Independently score one server-selected Flat ODF spreadsheet artifact.

    Read the Flat ODF XML; reject ambiguous structures, repeated populated or
    covered cells, formulas, and any populated cell outside the expected set. No caller
    path is accepted by the public API; callers must pass the server-owned file.
    """
    try:
        artifact = Path(path)
        if not artifact.is_file() or artifact.is_symlink():
            return {'status':'unknown','task_success':None,'reason':'artifact_missing_or_unsafe'}
        data = artifact.read_bytes()
        return verify_saved_fods_bytes(data, expected=expected)
    except (OSError, ValueError, InvalidOperation, KeyError,
            ET.ParseError, RuntimeError) as error:
        return {'status':'unknown','task_success':None,
                'reason':'artifact_unreadable_or_ambiguous',
                'error_type':type(error).__name__}


def verify_saved_fods_bytes(data, *, expected=None):
    """Score an already custody-checked Flat ODF byte snapshot."""
    try:
        expected = validate_calc_task_values(expected)
        if not isinstance(data, bytes) or not data or len(data) > 64 * 1024 * 1024:
            raise ValueError('artifact size outside bounds')
        if b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
            raise _UnscorableArtifact('xml_entities_refused')
        root = ET.fromstring(data)
        sheets = root.findall('.//office:body/office:spreadsheet/table:table', _ODS_NS)
        if len(sheets) != 1:
            raise _UnscorableArtifact('sheet_count_ambiguous')
        if sheets[0].find('.//table:covered-table-cell', _ODS_NS) is not None:
            raise _UnscorableArtifact('covered_cells_unsupported')
        values = {}
        row_index = 1
        for row in sheets[0].findall('table:table-row', _ODS_NS):
            row_repeat = int(row.attrib.get(
                '{%s}number-rows-repeated' % _ODS_NS['table'], '1'))
            if not 1 <= row_repeat <= 1_000_000:
                raise ValueError('row repeat outside bounds')
            column_index = 1
            row_values = {}
            cells = row.findall('table:table-cell', _ODS_NS)
            for cell in cells:
                col_repeat = int(cell.attrib.get(
                    '{%s}number-columns-repeated' % _ODS_NS['table'], '1'))
                if not 1 <= col_repeat <= 1_000_000:
                    raise ValueError('column repeat outside bounds')
                if cell.attrib.get('{%s}formula' % _ODS_NS['table']) is not None:
                    raise _UnscorableArtifact('formula_cells_unsupported')
                value_type = cell.attrib.get('{%s}value-type' % _ODS_NS['office'])
                value = cell.attrib.get('{%s}value' % _ODS_NS['office'])
                paragraphs = cell.findall('.//text:p', _ODS_NS)
                text_value = '\n'.join(''.join(p.itertext()) for p in paragraphs)
                if value_type in ('float', 'currency', 'percentage'):
                    if value is not None:
                        numeric = Decimal(value)
                        if not numeric.is_finite():
                            raise ValueError('non-finite numeric cell')
                    populated = value is not None
                    normalized = format(numeric, 'f') if value is not None else None
                elif value_type == 'string':
                    populated = bool(text_value)
                    normalized = text_value
                elif value_type in (None, 'boolean', 'date', 'time'):
                    populated = value is not None or bool(text_value)
                    normalized = text_value or value
                else:
                    raise _UnscorableArtifact('cell_value_type_unsupported')
                if populated:
                    if col_repeat != 1 or row_repeat != 1:
                        raise _UnscorableArtifact('repeated_populated_cells_ambiguous')
                    name = ''
                    col = column_index
                    while col:
                        col, rem = divmod(col - 1, 26)
                        name = chr(65 + rem) + name
                    name += str(row_index)
                    row_values[name] = normalized
                column_index += col_repeat
            if row_values and row_repeat != 1:
                raise _UnscorableArtifact('repeated_populated_rows_ambiguous')
            values.update(row_values)
            row_index += row_repeat
        if set(values) != set(expected):
            return {'status':'failed','task_success':False,
                    'reason':'populated_cell_set_mismatch','cells':values,
                    'artifact_sha256':hashlib.sha256(data).hexdigest()}
        def matches(name, wanted):
            actual = values[name]
            if actual is None or wanted is None:
                return actual == wanted
            try:
                return Decimal(actual) == Decimal(str(wanted))
            except InvalidOperation:
                return actual == str(wanted)
        if any(not matches(name, value) for name, value in expected.items()):
            return {'status':'failed','task_success':False,
                    'reason':'cell_value_mismatch','cells':values,
                    'artifact_sha256':hashlib.sha256(data).hexdigest()}
        return {'status':'verified','task_success':True,'cells':values,
                'artifact_sha256':hashlib.sha256(data).hexdigest(),
                'artifact_bytes':len(data)}
    except _UnscorableArtifact as error:
        return {'status':'unknown','task_success':None,
                'reason':str(error)}
    except (OSError, ValueError, InvalidOperation, KeyError,
            ET.ParseError, RuntimeError) as error:
        return {'status':'unknown','task_success':None,
                'reason':'artifact_unreadable_or_ambiguous',
                'error_type':type(error).__name__}


def _cell_cue(tsv, *, coordinate_origin=(0, 0), coordinate_scale=1,
              expected=None):
    expected = validate_calc_task_values(expected)
    found = {name: [] for name in _CELL_BOXES}
    if (not isinstance(coordinate_origin, (tuple, list)) or len(coordinate_origin) != 2
            or any(type(value) is not int for value in coordinate_origin)
            or type(coordinate_scale) is not int or coordinate_scale <= 0):
        return 'unknown'
    try:
        rows = csv.DictReader(io.StringIO(tsv), delimiter='\t')
        if not rows.fieldnames or any(name not in rows.fieldnames for name in _TSV_HEADER):
            return 'unknown'
        for row in rows:
            text = row.get('text', '').strip()
            if not text:
                continue
            x, y, width, height = (int(row[key]) for key in
                                   ('left', 'top', 'width', 'height'))
            if coordinate_scale != 1:
                x = coordinate_origin[0] + x // coordinate_scale
                y = coordinate_origin[1] + y // coordinate_scale
                width = (width + coordinate_scale - 1) // coordinate_scale
                height = (height + coordinate_scale - 1) // coordinate_scale
            else:
                x += coordinate_origin[0]
                y += coordinate_origin[1]
            confidence = float(row['conf'])
            if (width <= 0 or height <= 0 or not math.isfinite(confidence)
                    or not 0 <= confidence <= 100):
                return 'unknown'
            owners = [name for name, (left, top, right, bottom) in _CELL_BOXES.items()
                      if x >= left and y >= top and x + width <= right
                      and y + height <= bottom]
            if len(owners) > 1:
                return 'unknown'
            if owners:
                if confidence < 90 or not re.fullmatch(r'[0-9]+', text):
                    return 'unknown'
                found[owners[0]].append(text)
    except (ValueError, KeyError, TypeError, AttributeError):
        return 'unknown'
    if any(len(values) != 1 for values in found.values()):
        return 'unknown'
    return ('filled' if all(found[name] == [value]
                            for name, value in expected.items()) else 'wrong')


class CalcPrimaryProfile:
    def __init__(self, bridge, bindings, call_root, *, reviewed_sequence,
                 reviewed_artifact_sha256, blank_reviewed,
                 clock=time.monotonic_ns, ocr_runner=None, call_id=None,
                 attempt_id=None, task_artifact=None, task_values=None):
        if type(blank_reviewed) is not bool or blank_reviewed is not True:
            raise ValueError('fresh blank-sheet review is required')
        if type(reviewed_sequence) is not int or reviewed_sequence <= 0:
            raise ValueError('reviewed observation sequence is required')
        if (type(reviewed_artifact_sha256) is not str
                or not re.fullmatch(r'[0-9a-f]{64}', reviewed_artifact_sha256)):
            raise ValueError('reviewed PNG SHA-256 is required')
        if (not isinstance(bindings, dict) or set(bindings) != {'entry', 'save'}
                or any(not isinstance(bindings[name], dict)
                       or set(bindings[name]) != {'alias', 'offset'}
                       for name in ('entry', 'save'))):
            raise ValueError('profile requires exactly entry and save bindings')
        for name in ('entry', 'save'):
            binding = bindings[name]
            alias, offset = binding['alias'], binding['offset']
            if (type(alias) is not str or not re.fullmatch(r'[a-z][a-z0-9_]{0,31}', alias)
                    or not isinstance(offset, list) or len(offset) != 2
                    or any(type(value) is not int or value < 0 for value in offset)):
                raise ValueError('invalid profile alias or offset')
        if bindings['entry']['alias'] == bindings['save']['alias']:
            raise ValueError('entry and save require separate reviewed aliases')

        self.bridge = bridge
        self.clock = clock
        self.started_ns = clock()
        self.deadline_ns = self.started_ns + _MAX_RUNTIME_NS
        self.call_root = Path(call_root).resolve()
        self.evidence_root = self.call_root / 'calc-ocr'
        self.evidence_root.mkdir(parents=True, exist_ok=False)
        self.ocr_runner = ocr_runner or subprocess.run
        self.ocr_executable = shutil.which('tesseract')
        if not self.ocr_executable:
            raise ValueError('trusted Tesseract executable is unavailable')

        if bridge.sequence != reviewed_sequence or reviewed_sequence not in bridge.history:
            raise ValueError('reviewed source is no longer current')
        native, image = bridge.history[reviewed_sequence]
        artifact = native.get('native', {}).get('artifact', {})
        if (artifact.get('sha256') != reviewed_artifact_sha256
                or image.mode != 'RGB' or image.size != (_WIDTH, _HEIGHT)):
            raise ValueError('reviewed source identity or geometry changed')
        self.reviewed_binding = bridge._binding()
        self.reviewed_scope = bridge.scope
        self.reviewed_revision = bridge.binding_revision
        self.reviewed_window_id = self.reviewed_binding.get('surface')
        self.task_artifact = task_artifact
        self.task_values = validate_calc_task_values(
            task_artifact.expected_values if task_values is None
            and task_artifact is not None else task_values)
        if (task_artifact is not None
                and task_artifact.expected_values != self.task_values):
            raise ValueError('Calc task values differ from prepared artifact custody')
        self.task_save_request = None
        if (task_artifact is not None
                and (getattr(task_artifact, 'call_id', None) != call_id
                     or getattr(task_artifact, 'attempt_id', None) != attempt_id)):
            raise ValueError('pre-admitted artifact does not match this attempt')
        if call_id is not None or attempt_id is not None:
            from runtime.guarded_x11_v1.calc_task_artifact_v1 import CalcTaskArtifact
            process_incarnation_before = bridge.inspect_process_incarnation(
                self.reviewed_window_id)
            metadata = bridge.inspect_window_metadata(self.reviewed_window_id)
            process_incarnation_after = bridge.inspect_process_incarnation(
                self.reviewed_window_id)
            process_generation = self.reviewed_binding.get('process_generation')
            if (metadata.get('xid') != self.reviewed_window_id
                    or metadata.get('process_incarnation') != process_incarnation_before
                    or process_incarnation_after != process_incarnation_before
                    or metadata.get('process_generation') != process_generation
                    or type(metadata.get('window_incarnation')) is not str
                    or not re.fullmatch(r'[0-9a-f]{64}',
                                        metadata['window_incarnation'])
                    or metadata.get('mapped') is not True
                    or metadata.get('focused_before') is not True
                    or metadata.get('focused_after') is not True):
                raise ValueError('Calc artifact target generation is not current and focused')
            if self.task_artifact is None:
                self.task_artifact = CalcTaskArtifact(self.call_root,
                    call_id=call_id, attempt_id=attempt_id,
                    process_generation=process_generation,
                    window_generation=metadata['window_incarnation'],
                    target_xid=metadata['xid'],target_pid=metadata['process_pid'],
                target_start_ticks=metadata['process_start_ticks'],
                expected_values=self.task_values,
                    clock=clock)
            elif (self.task_artifact.process_generation is None
                    and self.task_artifact.window_generation is None):
                self.task_artifact.bind_target(
                    process_generation=process_generation,
                    window_generation=metadata['window_incarnation'],
                    target_xid=metadata['xid'],target_pid=metadata['process_pid'],
                    target_start_ticks=metadata['process_start_ticks'])
            elif (self.task_artifact.process_generation != process_generation
                    or self.task_artifact.window_generation
                        != metadata['window_incarnation']):
                raise ValueError('pre-admitted artifact target generation changed')
            self.task_process_generation = process_generation
            self.task_window_generation = metadata['window_incarnation']
        self.reviewed_title = bridge._window_title()
        if not isinstance(self.reviewed_title, str) or 'LibreOffice Calc' not in self.reviewed_title:
            raise ValueError('fresh reviewed source is not a LibreOffice Calc main sheet')
        self.entry_alias = bindings['entry']['alias']
        self.save_alias = bindings['save']['alias']
        entry_resolution = bridge.store.resolve_point(
            self.entry_alias, bindings['entry']['offset'], native, image,
            clock(), session_scope=self.reviewed_scope)
        entry_box = [4, 23, 24, 16]
        entry_offset = [12, 8]
        if not (entry_resolution.get('eligible')
                and entry_resolution.get('point') == [16, 31]
                and entry_resolution.get('observed_box') == entry_box
                and bindings['entry']['offset'] == entry_offset):
            raise ValueError('Calc entry must use the reviewed stable menu keyboard anchor')
        self.blank_pixels = {name: image.crop(box).tobytes()
                             for name, box in _CELL_BOXES.items()}
        role_bindings = {
            'enter': {'interaction': 'keyboard',
                      'offset': list(bindings['entry']['offset']),
                      'tail': [
                          {'op': 'text', 'text': self.task_values['A1'], 'gap_ms': 1},
                          {'op': 'key_chord', 'keys': ['Return']},
                          {'op': 'wait_update', 'timeout_ms': 100},
                          {'op': 'text', 'text': self.task_values['A2'], 'gap_ms': 1},
                          {'op': 'key_chord', 'keys': ['Return']},
                          {'op': 'wait_update', 'timeout_ms': 100}]},
            'save': {'interaction': 'keyboard',
                     'offset': list(bindings['save']['offset']),
                     'tail': [{'op': 'key_chord', 'keys': ['CTRL', 's']},
                              {'op': 'wait_update', 'timeout_ms': 100}]}}
        self.symbolic_plan_binding = None
        self.action_roles = {'enter':'enter', 'save':'save'}
        if self.task_artifact is not None and self.task_artifact.task_plan is not None:
            from runtime.guarded_x11_v1.compiled import surface
            self.symbolic_plan_binding = self.task_artifact.bind_task_plan(
                session_scope=self.reviewed_scope, surface=surface(self.bridge),
                target_aliases={'entry':self.entry_alias,'save':self.save_alias})
            self.interface = self.symbolic_plan_binding['interface']
            self.action_roles = {}
            self.bindings = {}
            for action_name, action in self.interface['actions'].items():
                role = 'enter' if action['operation'] == 'enter_pair' else 'save'
                self.action_roles[action_name] = role
                self.bindings[action_name] = role_bindings[role]
        else:
            self.bindings = role_bindings
            self.interface = self._interface(bindings)
        self.seen_sequences = set()
        self.ocr_count = 0
        self.evidence_count = 0

    def _interface(self, references):
        from runtime.guarded_x11_v1.compiled import surface
        def branch(when, action, next_state):
            return {'when': when, 'outcome': 'action', 'action': action,
                    'next_state': next_state, 'reason': None}
        entry_symbol = {
            'kind': 'target_reference',
            'target_reference': references['entry']['alias'],
            'identity_predicate': 'context_ok',
            'dependencies': ['context_ok']}
        save_symbol = {
            'kind': 'target_reference',
            'target_reference': references['save']['alias'],
            'identity_predicate': 'context_ok',
            'dependencies': ['context_ok', 'cells_filled']}
        from runtime.core_v1.compiled_gui import validate
        return validate({
            'format': 'compiled-gui-interface-v1',
            'interface_id': PROFILE_ID,
            'session_scope': self.reviewed_scope,
            'surface': surface(self.bridge),
            'predicates': ['context_ok', 'blank', 'cells_filled'],
            'symbols': {'entry': entry_symbol, 'save': save_symbol},
            'actions': {
                'enter': {'target_symbol': 'entry', 'operation': 'enter_pair',
                          'expected_effect': {'cells_filled': True}},
                'save': {'target_symbol': 'save', 'operation': 'request_save',
                         'expected_effect': {'cells_filled': True}}},
            'method': {
                'name': PROFILE_ID, 'version': '1',
                'initial_state': 'initial', 'max_transitions': 2,
                'max_runtime_ms': 10000,
                'states': {
                    'initial': {'branches': [branch(
                        {'context_ok': True, 'blank': True}, 'enter', 'filled')]},
                    'filled': {'branches': [branch(
                        {'context_ok': True, 'cells_filled': True}, 'save', 'handoff')]},
                    'handoff': {'branches': [{
                        'when': {'context_ok': True}, 'outcome': 'yield',
                        'action': None, 'next_state': None,
                        'reason': 'effect_unavailable'}]}}}})

    def _next_evidence_path(self):
        self.evidence_count += 1
        return self.evidence_root / f'{self.evidence_count:03d}'

    def _read_current(self, native, rgb, *, allow_active=False, run_ocr=True):
        now = self.clock()
        sequence = native.get('sequence')
        if (type(sequence) is not int or sequence <= 0 or sequence in self.seen_sequences
                or type(native.get('capture_ns')) is not int
                or not native['capture_ns'] <= now < self.deadline_ns
                or now - native['capture_ns'] > _MAX_AGE_NS):
            raise ValueError('stale, reused, or expired OCR source')
        self.seen_sequences.add(sequence)
        current = self.bridge._binding()
        if (self.bridge.scope != self.reviewed_scope
                or self.bridge.binding_revision != self.reviewed_revision
                or current != self.reviewed_binding
                or native.get('binding_revision') != self.reviewed_revision
                or native.get('pointer_binding') != self.reviewed_binding
                or native.get('native', {}).get('native_window_id') != self.reviewed_window_id
                or self.bridge.sequence != sequence
                or (self.bridge.active is not None and not allow_active)
                or self.bridge.review_required or self.bridge.session.recovery_required
                or not self.bridge._focus_within_target()):
            raise ValueError('Calc target association, focus, or recovery is uncertain')
        if allow_active:
            active_alias = (self.bridge.active[0]
                            if isinstance(self.bridge.active, tuple) else None)
            if active_alias not in {self.entry_alias, self.save_alias}:
                raise ValueError('active guarded alias is outside this Calc profile')
        title = self.bridge._window_title()
        if title != self.reviewed_title:
            raise ValueError('Calc main-sheet title changed after review')
        meta = native.get('native', {})
        artifact = meta.get('artifact', {})
        if (meta.get('frame') != 'screen_physical_px'
                or meta.get('region') != [0, 0, _WIDTH, _HEIGHT]
                or [meta.get('width'), meta.get('height')] != [_WIDTH, _HEIGHT]
                or [artifact.get('width'), artifact.get('height')] != [_WIDTH, _HEIGHT]
                or artifact.get('mime_type') != 'image/png'
                or type(artifact.get('bytes')) is not int
                or not 0 < artifact['bytes'] <= _MAX_OCR_BYTES):
            raise ValueError('unreviewed Calc capture geometry or artifact')
        path = Path(artifact['path']).resolve()
        if not path.is_relative_to(self.call_root):
            raise ValueError('OCR image is outside the exact call directory')
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if (digest != artifact.get('sha256') or len(data) != artifact['bytes']
                or artifact.get('source_raw_sha256') != meta.get('sha256')):
            raise ValueError('OCR image identity mismatch')
        decoded = Image.open(io.BytesIO(data)); decoded.load(); decoded = decoded.convert('RGB')
        if (rgb.mode != 'RGB' or rgb.size != (_WIDTH, _HEIGHT)
                or decoded.size != rgb.size or decoded.tobytes() != rgb.tobytes()):
            raise ValueError('OCR RGB handoff differs from the retained PNG')
        if not native['capture_ns'] <= meta['capture_ended_ns'] <= now:
            raise ValueError('capture interval is invalid')
        budget = min(1.0, (self.deadline_ns - now) / 1_000_000_000,
                     (native['capture_ns'] + _MAX_AGE_NS - now) / 1_000_000_000)
        if budget <= 0:
            raise ValueError('OCR has no bounded freshness budget')
        if not run_ocr:
            prefix = self._next_evidence_path()
            record = {'profile_id': PROFILE_ID, 'sequence': sequence,
                      'artifact_sha256': digest, 'ocr_status': 'not_run',
                      'ocr_invoked': False,
                      'reason': 'guard_predicates_exclude_cells_filled',
                      'input_dispatched': False, 'authority_granted': False}
            prefix.with_suffix('.json').write_text(
                json.dumps(record, sort_keys=True, allow_nan=False) + '\n', encoding='utf-8')
            return 'unknown'
        self.ocr_count += 1
        prefix = self._next_evidence_path()
        # The fixed 731/864 cells are only 90x34 pixels. Whole-screen PSM 11
        # produced correct text below the unchanged 90-point confidence gate.
        # Crop both cells from this exact guarded capture and OCR them together.
        crop_origin = (36, 143)
        cell_crop = ImageOps.autocontrast(
            rgb.crop((36, 143, 126, 177)).convert('L'), cutoff=1)
        cell_crop = cell_crop.resize(
            (cell_crop.width * 2, cell_crop.height * 2), Image.Resampling.LANCZOS)
        ocr_buffer = io.BytesIO()
        cell_crop.save(ocr_buffer, format='PNG')
        ocr_data = ocr_buffer.getvalue()
        ocr_digest = hashlib.sha256(ocr_data).hexdigest()
        command = [self.ocr_executable, 'stdin', 'stdout', '--psm', '6',
                   '-c', 'tessedit_char_whitelist=0123456789', 'tsv']
        try:
            result = self.ocr_runner(command, input=ocr_data, capture_output=True,
                                     timeout=budget, check=False)
        except subprocess.TimeoutExpired as error:
            record = {'profile_id': PROFILE_ID, 'sequence': sequence,
                      'artifact_sha256': digest, 'ocr_status': 'unknown',
                      'ocr_invoked': True,
                      'reason': 'timeout', 'started_ns': now,
                      'ocr_input_sha256': ocr_digest,
                      'ocr_transform': {'crop': [36, 143, 90, 34], 'scale': 2,
                                        'psm': 6, 'whitelist': '0123456789'},
                      'ended_ns': self.clock(), 'input_dispatched': False,
                      'authority_granted': False}
            (prefix.with_suffix('.tsv')).write_bytes(error.stdout or b'')
            (prefix.with_suffix('.stderr')).write_bytes(error.stderr or b'')
            (prefix.with_suffix('.json')).write_text(
                json.dumps(record, sort_keys=True, allow_nan=False) + '\n', encoding='utf-8')
            raise
        (prefix.with_suffix('.tsv')).write_bytes(result.stdout or b'')
        (prefix.with_suffix('.stderr')).write_bytes(result.stderr or b'')
        if (result.returncode != 0 or len(result.stdout or b'') > 1024 * 1024
                or self.clock() >= self.deadline_ns):
            raise ValueError('bounded OCR did not return a current complete result')
        cue = _cell_cue((result.stdout or b'').decode('utf-8'),
                        coordinate_origin=crop_origin, coordinate_scale=2,
                        expected=self.task_values)
        record = {'profile_id': PROFILE_ID, 'sequence': sequence,
                  'artifact_sha256': digest, 'ocr_status': cue,
                  'ocr_invoked': True,
                  'ocr_input_sha256': ocr_digest,
                  'ocr_transform': {'crop': [36, 143, 90, 34], 'scale': 2,
                                    'psm': 6, 'whitelist': '0123456789'},
                  'started_ns': now, 'ended_ns': self.clock(),
                  'input_dispatched': False, 'extra_capture': False,
                  'authority_granted': False}
        (prefix.with_suffix('.json')).write_text(
            json.dumps(record, sort_keys=True, allow_nan=False) + '\n', encoding='utf-8')
        return cue

    def perceive(self, native, rgb):
        try:
            cue = self._read_current(native, rgb)
            context_ok = True
        except (OSError, ValueError, KeyError, TypeError,
                subprocess.TimeoutExpired) as error:
            cue = 'unknown'
            context_ok = False
            record = {'profile_id': PROFILE_ID,
                      'sequence': native.get('sequence') if isinstance(native, dict) else None,
                      'ocr_status': 'unknown', 'reason': type(error).__name__,
                      'input_dispatched': False, 'authority_granted': False}
            self._next_evidence_path().with_suffix('.json').write_text(
                json.dumps(record, sort_keys=True, allow_nan=False) + '\n', encoding='utf-8')
        blank = bool(context_ok and all(
            rgb.crop(box).tobytes() == self.blank_pixels[name]
            for name, box in _CELL_BOXES.items()))
        cells_filled = (True if cue == 'filled' else
                        False if cue == 'wrong' else 'unknown')
        effect_name = 'cells_match' if self.symbolic_plan_binding else 'cells_filled'
        predicates = {'context_ok': context_ok, 'blank': blank,
                      effect_name: cells_filled}
        return predicates

    def guard_perceive(self, native, rgb):
        """OCR the bridge's one fresh guard capture without recapturing or retrying."""
        sequence = native.get('sequence') if isinstance(native, dict) else None
        artifact = native.get('native', {}).get('artifact', {}) if isinstance(native, dict) else {}
        try:
            active_alias = (self.bridge.active[0]
                            if isinstance(self.bridge.active, tuple) else None)
            skip_ocr = active_alias == self.entry_alias
            cue = self._read_current(native, rgb, allow_active=True,
                                     run_ocr=not skip_ocr)
            context_ok = True
        except (OSError, ValueError, KeyError, TypeError,
                subprocess.TimeoutExpired) as error:
            cue, context_ok = 'unknown', False
            record = {'profile_id':PROFILE_ID, 'sequence':sequence,
                      'artifact_sha256':artifact.get('sha256'),
                      'ocr_status':'unknown','reason':type(error).__name__,
                      'input_dispatched':False,'authority_granted':False}
            self._next_evidence_path().with_suffix('.json').write_text(
                json.dumps(record, sort_keys=True, allow_nan=False) + '\n', encoding='utf-8')
        blank = bool(context_ok and all(
            rgb.crop(box).tobytes() == self.blank_pixels[name]
            for name, box in _CELL_BOXES.items()))
        cells_filled = (True if cue == 'filled' else
                        False if cue == 'wrong' else 'unknown')
        effect_name = 'cells_match' if self.symbolic_plan_binding else 'cells_filled'
        predicates = {'context_ok':context_ok, 'blank':blank,
                      effect_name:cells_filled}
        return predicates

    def verify_effect(self, request, _native, _rgb):
        action = request.get('action')
        observed = request.get('observation', {}).get('predicates', {})
        role = self.action_roles.get(action)
        effect_name = 'cells_match' if self.symbolic_plan_binding else 'cells_filled'
        if role == 'enter':
            status = ('succeeded' if observed.get(effect_name) is True else
                      'failed' if observed.get(effect_name) is False else 'unavailable')
        else:
            # Ctrl+S is a request only. The separate saved-file scorer is not
            # implemented by this profile and graph success stays unproven.
            status = 'unavailable'
        if (role == 'save'
                and self.task_artifact is not None
                and self.task_save_request is None):
            # The graph's save effect remains unavailable. This receipt records
            # only that the fixed-profile Ctrl+S action reached its verifier.
            self.task_save_request = self.task_artifact.record_save_request(
                process_generation=self.task_process_generation,
                window_generation=self.task_window_generation)
        return {'status': status,
                'evidence_ref': request.get('observation', {}).get('evidence_ref')}

    def verify_unchanged_effect(self, request, native, rgb):
        """Permit only the nonvisual Save receipt path on an unchanged frame."""
        if self.action_roles.get(request.get('action')) == 'save':
            return self.verify_effect(request, native, rgb)
        return {'status':'unavailable',
                'evidence_ref':request.get('observation', {}).get('evidence_ref')}
