"""Separate native Qt owner/consumer; consumer text is changed only by native paste."""
import argparse
import json
import sys
import time
from pathlib import Path
from PyQt5.QtCore import QByteArray, QEvent, QMimeData, QObject, QSocketNotifier
from PyQt5.QtWidgets import QApplication, QPlainTextEdit, QTextEdit

parser = argparse.ArgumentParser()
parser.add_argument('role', choices=['owner', 'consumer'])
parser.add_argument('case', type=Path)
parser.add_argument('output', type=Path)
args = parser.parse_args()
case = json.loads(args.case.read_text())
app = QApplication([])
if app.platformName() != 'xcb':
    raise RuntimeError('native xcb platform is required')
phase = 'setup'
events = []


def journal(kind, **data):
    row = {'kind': kind, 'phase': phase, 'monotonic_ns': time.monotonic_ns(), **data}
    events.append(row)
    with (args.output / (args.role + '.events.jsonl')).open('a') as stream:
        stream.write(json.dumps(row) + '\n')


class Mime(QMimeData):
    def retrieveData(self, mime, preferred):
        journal('mime_request', mime=mime, preferred_type=int(preferred))
        return super().retrieveData(mime, preferred)


class Filter(QObject):
    def eventFilter(self, obj, event):
        if obj is widget and event.type() in (QEvent.KeyPress, QEvent.KeyRelease):
            journal('key_press' if event.type() == QEvent.KeyPress else 'key_release',
                    key=int(event.key()), modifiers=int(event.modifiers()))
        return False


widget = None
if args.role == 'owner':
    mime = Mime()
    mime.setData('text/plain', QByteArray(case['plain'].encode()))
    mime.setData('text/html', QByteArray(case['html'].encode()))
    app.clipboard().setMimeData(mime)
    ready = {'role': 'owner', 'platform': app.platformName()}
else:
    widget = QTextEdit() if case['target'] == 'rich' else QPlainTextEdit()
    widget.setWindowTitle('clipboard-native-' + case['id'])
    widget.resize(500, 200)
    widget.show()
    widget.setFocus()
    event_filter = Filter()
    app.installEventFilter(event_filter)
    widget.textChanged.connect(lambda: journal('text_changed', text=widget.toPlainText()))
    ready = {'role': 'consumer', 'platform': app.platformName(), 'window': int(widget.winId())}
print(json.dumps(ready), flush=True)


def command():
    global phase
    line = sys.stdin.readline()
    if not line:
        app.quit()
        return
    request = json.loads(line)
    op = request['op']
    journal('ipc_command', op=op)
    response = {'op': op}
    if op == 'phase':
        phase = request['phase']
    elif op == 'probe':
        response['key_releases'] = [x['key'] for x in events if x['kind'] == 'key_release']
    elif op == 'dump' and widget is not None:
        text = widget.toPlainText()
        document = widget.document().toHtml()
        (args.output / 'text.txt').write_text(text)
        (args.output / 'document.html').write_text(document)
        app.primaryScreen().grabWindow(int(widget.winId())).save(str(args.output / 'window.png'))
        response['text'] = text
    elif op == 'stop':
        app.quit()
    else:
        raise RuntimeError('unsupported command')
    print(json.dumps(response), flush=True)


notifier = QSocketNotifier(sys.stdin.fileno(), QSocketNotifier.Read)
notifier.activated.connect(command)
raise SystemExit(app.exec_())
