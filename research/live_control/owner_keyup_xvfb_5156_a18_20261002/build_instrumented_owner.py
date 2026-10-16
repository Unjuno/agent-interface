from pathlib import Path
import hashlib

HERE = Path(__file__).resolve().parent
source_path = HERE / "dependencies" / "input_owner_v10.py"
source = source_path.read_text(encoding="utf-8")
source_sha = hashlib.sha256(source_path.read_bytes()).hexdigest()
expected = (HERE / "dependencies" / "SOURCE_SHA256.txt").read_text().splitlines()
pinned = next(line.split()[0] for line in expected if line.endswith(" input_owner_v10.py"))
if source_sha != pinned:
    raise SystemExit(f"STOP_SOURCE_HASH input_owner_v10 {source_sha} != {pinned}")

old = '''        def release(reason):
            nonlocal active,revision
            revision += 1
            for code in list(held):
                xtest.fake_input(d, X.KeyRelease, code)
            for button in list(buttons):
                xtest.fake_input(d, X.ButtonRelease, button)
            d.sync()
            mask = d.screen().root.query_pointer().mask
'''
new = '''        def release(reason):
            nonlocal active,revision
            revision += 1
            cleanup_rows = []
            cleanup_intent = getattr(active, "intent_token", None) if active is not None else None
            for code in list(held):
                release_request_ns = time.perf_counter_ns()
                xtest.fake_input(d, X.KeyRelease, code)
                cleanup_rows.append({"keycode": code, "intent_token": getattr(held[code], "intent_token", None),
                                     "release_request_ns": release_request_ns})
            for button in list(buttons):
                xtest.fake_input(d, X.ButtonRelease, button)
            d.sync()
            sync_return_ns = time.perf_counter_ns()
            for row in cleanup_rows:
                row["sync_return_ns"] = sync_return_ns
            mask = d.screen().root.query_pointer().mask
'''
if source.count(old) != 1:
    raise SystemExit(f"STOP_PATCH_RELEASE_BLOCK count={source.count(old)}")
source = source.replace(old, new)
old_record = '''            record = dict(event='owner_release', reason=reason, verified=not down and not buttons_down, buttons_down=buttons_down,
                          keys_down=down, verified_ns=time.perf_counter_ns(),
                          valid_until_ns=active.deadline if active else None)
'''
new_record = '''            record = dict(event='owner_release', reason=reason, owner_id=self.owner_id,
                          intent_token=cleanup_intent, verified=not down and not buttons_down,
                          buttons_down=buttons_down, keys_down=down, verified_ns=time.perf_counter_ns(),
                          valid_until_ns=active.deadline if active else None,
                          key_release_brackets=cleanup_rows)
'''
if source.count(old_record) != 1:
    raise SystemExit(f"STOP_PATCH_RELEASE_RECORD count={source.count(old_record)}")
source = source.replace(old_record, new_record)
old_up = '''                            if code in held:
                                xtest.fake_input(d, X.KeyRelease, code)
                                d.sync()
                                del held[code]
                            result = None
'''
new_up = '''                            if code in held:
                                release_request_ns = time.perf_counter_ns()
                                xtest.fake_input(d, X.KeyRelease, code)
                                d.sync()
                                sync_return_ns = time.perf_counter_ns()
                                self.records.append(dict(
                                    event="owner_explicit_key_up", owner_id=self.owner_id,
                                    intent_token=getattr(lease, "intent_token", None),
                                    keycode=code, release_request_ns=release_request_ns,
                                    sync_return_ns=sync_return_ns, grants_input_authority=False))
                                del held[code]
                            result = None
'''
if source.count(old_up) != 1:
    raise SystemExit(f"STOP_PATCH_EXPLICIT_UP count={source.count(old_up)}")
source = source.replace(old_up, new_up)
out = HERE / "dependencies" / "input_owner_v11.py"
out.write_text(source, encoding="utf-8", newline="\n")
print(f"PASS_PATCH source_sha256={source_sha} instrumented_sha256={hashlib.sha256(out.read_bytes()).hexdigest()}")
