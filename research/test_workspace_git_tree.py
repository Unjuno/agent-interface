"""Local temporary Git fixtures only; no repository payload or network."""
import contextlib
import importlib.util
import io
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import sys
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).with_name('check_workspace_index.py')
spec = importlib.util.spec_from_file_location('workspace_checker', SOURCE)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class CommittedTreeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.root = self.repo / 'research'
        self.root.mkdir()
        shutil.copy2(SOURCE, self.root / SOURCE.name)
        self.git('init', '-q')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')

    def git(self, *args, input=None):
        return subprocess.run(['git', '-C', str(self.repo), *args], input=input,
                              capture_output=True, check=True, timeout=5).stdout

    def prepare(self, actual=('a',), indexed=('a',)):
        for path in self.root.iterdir():
            if path.is_dir(): shutil.rmtree(path)
        for name in actual:
            p = self.root / name / 'nested' / 'payload.bin'
            p.parent.mkdir(parents=True)
            p.write_bytes(b'never read this payload')
        (self.root / 'README.md').write_text('\n'.join(f'[`{x}/`]({x}/)' for x in indexed))
        (self.root / 'ROOT_NAMESPACE_MAP.md').write_text('')
        self.commit()

    def commit(self):
        self.git('add', '--all')
        self.git('commit', '-qm', 'fixture', '--allow-empty')

    def run_checker(self, tree=False):
        with patch.object(checker, 'ROOT', self.root), patch.object(checker, 'INDEX_FILES', (self.root/'README.md', self.root/'ROOT_NAMESPACE_MAP.md')), patch('sys.argv', ['check_workspace_index.py'] + (['--git-tree'] if tree else [])), contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()) as err:
            result = checker.main()
        return result, out.getvalue(), err.getvalue()

    def test_same_commit_not_tampered_worktree(self):
        self.prepare()
        (self.root/'README.md').write_text('')
        self.assertEqual(self.run_checker()[0], 1)
        self.assertEqual(self.run_checker(True)[0], 0)

    def test_complete_missing_dangling_parity(self):
        for actual, indexed in [(('a',),('a',)), (('a','new'),('a',)), (('a',),('a','gone'))]:
            with self.subTest(actual=actual, indexed=indexed):
                self.prepare(actual,indexed)
                self.assertEqual(self.run_checker(True),self.run_checker())

    def test_hidden_regular_nested_unicode_and_tab(self):
        self.prepare(('a','.hidden','space name','日本語','tab\tname'), ('a','space name','日本語','tab\tname'))
        (self.root/'ordinary.txt').write_text('not a namespace')
        self.commit()
        self.assertEqual(self.run_checker(True),self.run_checker())

    def test_untracked_directory_excluded_only_in_tree_mode(self):
        self.prepare()
        (self.root/'untracked').mkdir()
        self.assertEqual(self.run_checker()[0],1)
        self.assertEqual(self.run_checker(True)[0],0)

    def test_symlink_entries_fail_closed(self):
        self.prepare()
        for target in ['a', 'README.md', 'missing', 'link']:
            with self.subTest(target=target):
                p=self.root/'link'
                if p.is_symlink(): p.unlink()
                p.symlink_to(target)
                self.commit()
                code,out,err=self.run_checker(True)
                self.assertEqual(code,2)
                self.assertIn('UNSUPPORTED_TREE_ENTRY',err)

    def test_hidden_symlink_ignored(self):
        self.prepare()
        (self.root/'.link').symlink_to('a')
        self.commit()
        self.assertEqual(self.run_checker(True),self.run_checker())

    def test_gitlink_fails_closed(self):
        self.prepare()
        oid=self.git('rev-parse','HEAD').decode().strip()
        self.git('update-index','--add','--cacheinfo',f'160000,{oid},research/module')
        self.git('commit','-qm','gitlink')
        self.assertEqual(self.run_checker(True)[0],2)

    def test_missing_doc_and_invalid_encoding_fail(self):
        self.prepare()
        (self.root/'ROOT_NAMESPACE_MAP.md').unlink()
        self.commit()
        self.assertEqual(self.run_checker(True)[0],2)
        (self.root/'ROOT_NAMESPACE_MAP.md').write_bytes(b'\xff')
        self.commit()
        self.assertEqual(self.run_checker(True)[0],2)

    def test_hidden_only_and_malformed_links_preserve_parity(self):
        self.prepare(('.hidden',),())
        (self.root/'README.md').write_text('[`a/`](b/) [`../x/`](../x/) [`https://x/`](https://x/)')
        self.commit()
        self.assertEqual(self.run_checker(True),self.run_checker())

    def test_sparse_filesystem_does_not_hide_namespace(self):
        self.prepare(('a','new'),('a',))
        shutil.rmtree(self.root/'new')
        self.assertEqual(self.run_checker()[0],0)
        code,out,_=self.run_checker(True)
        self.assertEqual(code,1)
        self.assertIn('new',out)

    def test_head_resolved_once_even_when_head_advances(self):
        self.prepare()
        original=checker.run_git
        calls=[]
        def racing(repo,args):
            calls.append(args)
            result=original(repo,args)
            if args[0]=='rev-parse':
                p=self.root/'later'/'x'; p.parent.mkdir(); p.write_text('x')
                (self.root/'README.md').write_text('')
                self.commit()
            return result
        with patch.object(checker,'run_git',racing):
            self.assertEqual(self.run_checker(True)[0],0)
        self.assertEqual(sum(a[0]=='rev-parse' for a in calls),1)

    def test_missing_root_and_git_error_fail(self):
        self.prepare()
        self.git('rm','-qr','research')
        self.git('commit','-qm','remove root')
        self.assertEqual(self.run_checker(True)[0],2)
        shutil.rmtree(self.repo/'.git')
        self.assertEqual(self.run_checker(True)[0],2)

    def test_document_symlink_rejected(self):
        self.prepare()
        (self.root/'README.md').unlink()
        (self.root/'README.md').symlink_to('ROOT_NAMESPACE_MAP.md')
        self.commit()
        self.assertEqual(self.run_checker(True)[0],2)

    def test_mixed_object_id_lengths_rejected(self):
        self.prepare()
        original=checker.run_git
        def corrupt(repo,args):
            result=original(repo,args)
            if args[0]=='ls-tree':
                header,tail=result.split(b'\t',1)
                parts=header.split(b' ')
                parts[2]=b'a'*64
                return b' '.join(parts)+b'\t'+tail
            return result
        with patch.object(checker,'run_git',corrupt):
            with self.assertRaisesRegex(checker.TreeInventoryError,'OBJECT_ID_LENGTH_MISMATCH'):
                checker.committed_inventory(self.repo)


class ParserAndBoundTests(unittest.TestCase):
    def test_parser_rejects_corruption(self):
        good=b'040000 tree '+b'a'*40+b'\tdir\0'
        bad=[good[:-1], good+good, good.replace(b'040000',b'100644'),
             good.replace(b'\tdir',b'\t../dir'), good.replace(b'a'*40,b'z'*40),
             good.replace(b'\tdir',b'\t\xff'), b'\0', b'bad\0']
        for data in bad:
            with self.subTest(data=data), self.assertRaises(checker.TreeInventoryError):
                checker.parse_tree(data)

    def test_parser_preserves_tabs_newlines_unicode(self):
        name='日本\t語\nline'
        data=b'040000 tree '+b'a'*40+b'\t'+name.encode()+b'\0'
        self.assertIn(name,checker.parse_tree(data))

    def test_real_child_output_limit_and_timeout(self):
        popen=subprocess.Popen
        def child(code):
            return lambda *a,**kw:popen([sys.executable,'-c',code],**kw)
        with patch.object(checker.subprocess,'Popen',child("import sys; sys.stdout.write('x'*4096)")), patch.object(checker,'OUTPUT_LIMIT',100):
            with self.assertRaisesRegex(checker.TreeInventoryError,'GIT_OUTPUT_LIMIT'):
                checker.run_git(Path('.'),['ignored'])
        with patch.object(checker.subprocess,'Popen',child('import time; time.sleep(2)')), patch.object(checker,'GIT_TIMEOUT',0.05):
            with self.assertRaisesRegex(checker.TreeInventoryError,'GIT_TIMEOUT'):
                checker.run_git(Path('.'),['ignored'])

    def test_missing_git_and_nonzero_fail(self):
        with patch.object(checker.subprocess,'Popen',side_effect=FileNotFoundError):
            with self.assertRaisesRegex(checker.TreeInventoryError,'GIT_START_FAILED'):
                checker.run_git(Path('.'),[])
        with self.assertRaisesRegex(checker.TreeInventoryError,'GIT_COMMAND_FAILED'):
            checker.run_git(Path('.'),['not-a-real-git-command'])


if __name__=='__main__': unittest.main()
