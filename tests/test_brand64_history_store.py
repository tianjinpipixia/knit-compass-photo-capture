import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import brand64_history_store as history
import restore_brand64_valid_state as restore
import publish_brand64_flash_feed as publisher


class HistoryStoreTests(unittest.TestCase):
    def test_legacy_history_roundtrip_is_lossless_and_every_blob_is_bounded(self):
        events = {str(i): {'observed_date':'2026-11-06', '原文':'ニット'*60, 'previous_values':{'price':i}}
                  for i in range(1000)}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/history.INDEX).write_text(json.dumps(events, ensure_ascii=False))
            self.assertEqual(history.read_history(root), events)
            names = history.write_history(root, events, max_part_bytes=1024)
            self.assertEqual(history.read_history(root), events)
            self.assertEqual(set(names), set(history.history_files(root)))
            self.assertTrue(all((root/name).stat().st_size <= 1024 for name in names if name != history.INDEX))
            before = (root/history.INDEX).read_bytes()
            history.write_history(root, events, max_part_bytes=1024)
            self.assertEqual((root/history.INDEX).read_bytes(), before)

    def test_missing_corrupt_duplicate_or_unsafe_parts_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            history.write_history(root, {'a':{'original':True}})
            index_path = root/history.INDEX
            raw = index_path.read_bytes()
            index = json.loads(raw)
            part = root/index['parts'][0]['path']
            original = part.read_bytes()
            part.unlink()
            with self.assertRaises(FileNotFoundError): history.read_history(root)
            part.write_bytes(original+b' ')
            with self.assertRaisesRegex(ValueError, 'checksum'): history.read_history(root)
            part.write_bytes(original)
            index['parts'].append(index['parts'][0])
            index_path.write_text(json.dumps(index))
            with self.assertRaisesRegex(ValueError, 'duplicate'): history.read_history(root)
            index = json.loads(raw); index['parts'][0]['path'] = '../outside.json'
            index_path.write_text(json.dumps(index))
            with self.assertRaisesRegex(ValueError, 'path'): history.read_history(root)

    def test_failed_index_replacement_leaves_previous_checkpoint_readable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old = {'a':{'original':'exact original'}}
            history.write_history(root, old)
            real_write = history.atomic_write
            def fail_index(path, raw):
                if path.name == history.INDEX: raise OSError('disk unavailable')
                return real_write(path, raw)
            with patch.object(history, 'atomic_write', side_effect=fail_index):
                with self.assertRaises(OSError): history.write_history(root, {**old, 'b':{'new':True}})
            self.assertEqual(history.read_history(root), old)

    def test_restore_copies_parts_and_rejects_broken_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, target = Path(tmp)/'source', Path(tmp)/'target'
            source.mkdir()
            events = {'a':{'original':'日本語'}}
            history.write_history(source, events)
            (source/'known-products.json').write_text(json.dumps({str(i):{} for i in range(500)}))
            self.assertTrue(restore.validate_candidate(source, 'fixture'))
            with patch.object(restore, 'ROOT', target): restore.copy_state(source, 'fixture')
            self.assertEqual(history.read_history(target), events)
            (source/json.loads((source/history.INDEX).read_bytes())['parts'][0]['path']).unlink()
            self.assertFalse(restore.validate_candidate(source, 'broken'))

    def test_git_ref_extraction_includes_history_parts(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, checkout, output = Path(tmp)/'repo', Path(tmp)/'checkout', Path(tmp)/'out'
            subprocess.run(['git','init','-q',str(repo)],check=True)
            source = repo/restore.ROOT
            source.mkdir(parents=True)
            events = {'fixture':{'observed_date':'2026-11-06'}}
            history.write_history(source, events)
            subprocess.run(['git','-C',str(repo),'add','.'],check=True)
            subprocess.run(['git','-C',str(repo),'-c','user.name=Test','-c','user.email=test@example.invalid','commit','-qm','fixture'],check=True)
            subprocess.run(['git','clone','-q',str(repo),str(checkout)],check=True)
            def in_checkout(*args, **kwargs):
                return subprocess.run(args,check=kwargs.get('check',True),text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=checkout)
            def bytes_in_checkout(*args, **kwargs):
                return subprocess.run(args,check=kwargs.get('check',True),stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=checkout)
            with patch.object(restore,'run',side_effect=in_checkout), patch.object(restore,'run_bytes',side_effect=bytes_in_checkout):
                self.assertTrue(restore.extract_ref('HEAD',output))
            self.assertEqual(history.read_history(output),events)

    def test_publication_git_tree_keeps_exact_history_and_removes_obsolete_parts(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, remote = Path(tmp)/'repo', Path(tmp)/'remote.git'
            subprocess.run(['git','init','-q','--bare',str(remote)],check=True)
            subprocess.run(['git','init','-q',str(repo)],check=True)
            for key,value in [('user.name','Test'),('user.email','test@example.invalid')]:
                subprocess.run(['git','-C',str(repo),'config',key,value],check=True)
            subprocess.run(['git','-C',str(repo),'remote','add','origin',str(remote)],check=True)
            (repo/'config').mkdir()
            (repo/'config/brand64-active-brands.json').write_text('{"active_brands":{}}')
            root = repo/publisher.PREFIX
            root.mkdir(parents=True)
            for name in [*publisher.STATE_FILES,'feed.json','latest.json','flash-latest.json','retrospective-merge-summary.json']:
                (root/name).write_text('{}')
            (root/'summary.md').write_text('fixture')
            (root/'cumulative-products').mkdir()
            (root/'cumulative-products/review-queue.json').write_text('[]')
            events={'a':{'original':'kept'}}
            (root/history.INDEX).write_text(json.dumps(events))
            previous = Path.cwd()
            try:
                os.chdir(repo)
                with patch.object(publisher,'seed_working_state',return_value={}), \
                     patch.object(publisher,'merge_retrospective_sources',return_value={'source_record_count':0}), \
                     patch.object(publisher,'build_observed_product_shards',return_value=[]), \
                     patch.object(publisher,'build_cumulative_product_shards',return_value=[]):
                    publisher.publish(root)
                    first=set(history.history_files(root))
                    events['a']['original']='updated; prior fixture retained by test'
                    events['b']={'second':True}
                    history.write_history(root,events)
                    publisher.publish(root)
                def git(*args):
                    return subprocess.run(['git',*args],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).stdout
                names=git('ls-tree','-r','--name-only','refs/remotes/origin/'+publisher.BRANCH).decode().splitlines()
                current=set(history.history_files(root))
                self.assertTrue(all(publisher.PREFIX+n in names for n in current))
                self.assertTrue(all(publisher.PREFIX+n not in names for n in first-current))
                target=Path(tmp)/'readback'
                for name in current:
                    (target/name).parent.mkdir(parents=True,exist_ok=True)
                    (target/name).write_bytes(git('show','refs/remotes/origin/'+publisher.BRANCH+':'+publisher.PREFIX+name))
                self.assertEqual(history.read_history(target),events)
            finally:
                os.chdir(previous)


if __name__ == '__main__': unittest.main()
