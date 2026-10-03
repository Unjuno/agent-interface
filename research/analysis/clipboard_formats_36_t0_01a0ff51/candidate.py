"""Actual Qt paste fixture; judgments are diagnostic, never input authority."""
import argparse
import hashlib
import json
import os
import platform
import time
from pathlib import Path

from PyQt5.QtCore import QMimeData, QT_VERSION_STR, PYQT_VERSION_STR
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QApplication, QPlainTextEdit, QTextEdit

import gates


def digest(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


class TracedMime(QMimeData):
    def __init__(self, plain, html):
        super().__init__()
        self.requests = []
        if plain is not None:
            self.setData('text/plain', plain.encode('utf-8'))
        if html is not None:
            self.setData('text/html', html.encode('utf-8'))

    def retrieveData(self, mime, preferred):
        self.requests.append(mime)
        return super().retrieveData(mime, preferred)


class PlainPreference(QTextEdit):
    def insertFromMimeData(self, source):
        self.insertPlainText(source.text())


class SanitizingTarget(QTextEdit):
    def insertFromMimeData(self, source):
        self.insertHtml(source.html().replace('<b>', '').replace('</b>', ''))


def metadata(case, reference=False):
    prefix = 'reference_' if reference else ''
    plain, html = case[prefix + 'plain'], case[prefix + 'html']
    return {
        'generation': case['generation'] if reference else case['current_generation'],
        'owner': 'fixture-source' if reference else case['current_owner'],
        'scope': 'private-offscreen-fixture',
        'summary': digest(plain) if plain is not None else None,
        'formats': [[mime, digest(value)] for mime, value in [('text/plain', plain), ('text/html', html)] if value is not None],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cases', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    if os.environ.get('QT_QPA_PLATFORM') != 'offscreen':
        raise RuntimeError('offscreen platform is required before QApplication')
    runtime = Path('/tmp/clipboard36-runtime')
    runtime.mkdir(mode=0o700, exist_ok=True)
    os.environ['XDG_RUNTIME_DIR'] = str(runtime)
    app = QApplication([])
    if app.platformName() != 'offscreen':
        raise RuntimeError('host clipboard is not an eligible fixture')
    clip = app.clipboard()
    rows = []
    started = time.monotonic_ns()
    for case in json.loads(args.cases.read_text())['cases']:
        mime = TracedMime(case['plain'], case['html'])
        clip.setMimeData(mime)
        target_class = {'rich': QTextEdit, 'plain': QPlainTextEdit, 'prefer_plain': PlainPreference, 'sanitize': SanitizingTarget}[case['target']]
        target = target_class()
        mime.requests.clear()
        if case['paste']:
            target.paste()
        app.processEvents()
        accessed = list(dict.fromkeys(x for x in mime.requests if x in ('text/plain', 'text/html')))
        reported = accessed if case['format_visible'] else []
        text = target.toPlainText()
        document = target.document()
        cursor = QTextCursor(document)
        cursor.setPosition(0)
        cursor.setPosition(len(text), QTextCursor.KeepAnchor)
        bold = bool(text) and cursor.charFormat().fontWeight() >= 75
        effect = {'text': text, 'bold': bold}
        folder = args.output / case['id']
        folder.mkdir()
        (folder / 'text.txt').write_bytes(text.encode('utf-8'))
        (folder / 'document.html').write_bytes(document.toHtml().encode('utf-8'))
        expected, observed = metadata(case, True), metadata(case)
        before = {arm: gates.precheck(arm, expected, observed) for arm in ('summary', 'manifest')}
        judgments = dict(before)
        for arm, require_format in [('format_effect', True), ('effect_only', False)]:
            judgments[arm] = before['manifest'] if before['manifest'] != 'ELIGIBLE' else gates.postcheck(case['paste'], reported, effect, case['contract'], require_format=require_format)
        rows.append({
            'id': case['id'], 'expected': expected, 'observed': observed,
            'paste_attempted': case['paste'], 'requested_formats': reported,
            'format_visibility': case['format_visible'], 'qt_effect': effect,
            'judgments': judgments,
            'saved': {name: hashlib.sha256((folder / name).read_bytes()).hexdigest() for name in ('text.txt', 'document.html')},
            'planner_metadata': observed,
        })
        target.deleteLater()
    clip.clear()
    app.processEvents()
    packet = {'schema': 'clipboard36-qt-diagnostic-v1', 'environment': {'qt': QT_VERSION_STR, 'pyqt': PYQT_VERSION_STR, 'python': platform.python_version(), 'machine': platform.machine(), 'platform_plugin': app.platformName(), 'selection_supported': clip.supportsSelection()}, 'elapsed_ns': time.monotonic_ns() - started, 'rows': rows}
    (args.output / 'raw.json').write_text(json.dumps(packet, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'rows': len(rows), 'qt': QT_VERSION_STR, 'platform': app.platformName()}))


if __name__ == '__main__':
    main()
