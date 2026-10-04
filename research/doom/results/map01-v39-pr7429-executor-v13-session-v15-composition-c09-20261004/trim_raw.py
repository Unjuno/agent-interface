from pathlib import Path
root=Path(r'''C:\Users\junny\Documents\Codex\2026-10-03\new-chat-3\work\pr59-cancel-cause-stack\research\doom\results\map01-v39-pr7429-executor-v13-session-v15-composition-c09-20261004''')
for path in (root/'raw').glob('*.txt'):
    text=path.read_text(encoding='utf-8-sig').rstrip()+"\n"
    path.write_text(text, encoding='utf-8')
