"""Disposable Qt fixture. Selection APIs are setup; replacement is native input only."""
import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from PyQt5 import QtCore, QtGui, QtWidgets


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--cell', required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    cell = json.loads(a.cell)
    a.output.mkdir(exist_ok=True)
    log = (a.output / 'events.jsonl').open('x', encoding='utf-8')
    def event(kind, **data):
        log.write(json.dumps(dict(kind=kind, ns=time.monotonic_ns(), **data), ensure_ascii=False) + '\n')
        log.flush()
    q = QtWidgets.QApplication([])
    base = QtWidgets.QPlainTextEdit if cell['widget'] == 'plain' else QtWidgets.QTextEdit
    class Edit(base):
        def keyPressEvent(self, e):
            event('key_press', key=e.key(), text=e.text(), auto=e.isAutoRepeat())
            super().keyPressEvent(e)
        def keyReleaseEvent(self, e):
            event('key_release', key=e.key(), text=e.text(), auto=e.isAutoRepeat())
            super().keyReleaseEvent(e)
    w = Edit()
    w.setPlainText(cell['current'])
    w.setWindowTitle('edit49-' + cell['cell_id'])
    w.resize(520, 160)
    changes = []
    def changed():
        changes.append(w.toPlainText())
        event('text_changed', text=w.toPlainText())
    w.textChanged.connect(changed)
    w.show()
    def snapshot():
        c = w.textCursor()
        return dict(text=w.toPlainText(), anchor=c.anchor(), position=c.position(),
                    selected=c.selectedText(), qt_document_count=w.document().characterCount(),
                    has_selection=c.hasSelection())
    def reply(data):
        print(json.dumps(data, ensure_ascii=False), flush=True)
    def receive():
        line = sys.stdin.readline()
        if not line:
            q.quit()
            return
        command = json.loads(line)
        event('command', command=command)
        if command['op'] == 'select':
            c = w.textCursor()
            c.setPosition(command['span'][0])
            c.setPosition(command['span'][1], QtGui.QTextCursor.KeepAnchor)
            w.setTextCursor(c)
            reply(dict(kind='selected', **snapshot()))
        elif command['op'] == 'save':
            def save():
                state = dict(kind='saved', **snapshot(), changes=changes)
                (a.output / 'saved.txt').write_bytes(state['text'].encode('utf-8'))
                (a.output / 'state.json').write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n')
                w.grab().save(str(a.output / 'widget.png'))
                event('saved', state=state)
                reply(state)
            QtCore.QTimer.singleShot(30, save)
        elif command['op'] == 'quit':
            q.quit()
        else:
            raise ValueError('unknown fixture command')
    notifier = QtCore.QSocketNotifier(sys.stdin.fileno(), QtCore.QSocketNotifier.Read)
    notifier.activated.connect(receive)
    QtCore.QTimer.singleShot(30, lambda: reply(dict(kind='ready', role='edit_fixture', pid=os.getpid(),
                                                  xid=int(w.winId()), qt=QtCore.QT_VERSION_STR,
                                                  pyqt=QtCore.PYQT_VERSION_STR, **snapshot())))
    q.exec_()
    event('exit')
    log.close()


if __name__ == '__main__':
    main()
