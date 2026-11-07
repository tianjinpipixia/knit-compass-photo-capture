import json
from pathlib import Path
import sys
import tempfile
import zipfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import prepare_brand64_recovery as recovery
import restore_brand64_valid_state as restore
from brand64_canonical_store import read_pool
from brand64_history_store import read_history
from publish_brand64_flash_feed import build_cumulative_product_shards


class RecoveryPreparationTests(unittest.TestCase):
    def fixture(self, root):
        scope=root/'scope.json'
        recovery.write(scope,{'status':'LOCKED_OWNER_APPROVED','scope_id':'TEST','target_brand_count':1,'records':[{'brand_id':'B'}]})
        sources=[]
        for label,day,codes in [('old','2026-11-05',['A']),('six','2026-11-06',['A','B']),('seven','2026-11-07',['A','C'])]:
            source=root/label;source.mkdir()
            records=[{'brand_id':'B','brand_name':'Brand','product_name':'Knit '+c,
                'product_url':'https://example.test/'+c,'product_code':c,
                'first_seen_date':day,'last_seen_date':day,'scope_status':'BRAND_AND_KNIT_PATH_MATCHED'} for c in codes]
            latest={'collector':'CHATGPT_OFFICIAL_DIRECT','observed_date':day,'generated_at_utc':day+'T01:00:00+00:00',
                'product_count':len(records),'product_observed_brand_count':1,'active_brand_count':1,'attempted_brand_count':1,
                'complete_brand_count':0,'publication_status':'PUBLISH_HOLD','human_review_required':True,'scan_status':'PARTIAL_COVERAGE',
                'brands':[{'brand_id':'B','product_count':len(records),'coverage':{'status':'INCOMPLETE'}}]}
            recovery.write(source/'latest.json',latest)
            recovery.write(source/'feed.json',{'summary':latest,'candidates':[]})
            recovery.write(source/'coverage-state.json',{'B':{'brand_name':'Brand','observed_date':day,'surface_items':records}})
            recovery.write(source/'known-products.json',{'B|'+r['product_url']:r for r in records})
            recovery.write(source/'flash-history.json',{label:{'observed_date':day,'original':label}})
            recovery.write(source/'flash-latest.json',{'candidates':[]})
            (source/'summary.md').write_text('Original '+day)
            build_cumulative_product_shards(source)
            sources.append({'label':label,'root':label,'files_sha256':{n:recovery.digest(source/n) for n in ['latest.json','feed.json','known-products.json','flash-history.json','coverage-state.json','cumulative-products/manifest.json']}})
        plan=root/'plan.json'
        recovery.write(plan,{'scope':{'path':'scope.json','scope_id':'TEST','sha256':recovery.digest(scope)},
            'expected_canonical_head':'a'*40,'sources':sources})
        return plan

    def test_older_only_products_and_events_survive_newest_daily_generation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);plan=self.fixture(root);out=root/'out'
            result=recovery.prepare(plan,out)
            self.assertEqual(result['product_count'],3)
            self.assertEqual(result['history_event_count'],3)
            self.assertEqual(result['daily_observation_source'],'seven')
            self.assertEqual(read_pool(out)['B|https://example.test/A']['first_seen_date'],'2026-11-05')
            self.assertEqual(recovery.read(out/'latest.json')['product_count'],2)
            self.assertIn('B|https://example.test/B',read_pool(out))
            self.assertEqual(set(read_history(out)),{'old','six','seven'})
            self.assertFalse(result['analysis_ready'])
            recovery.verify_review(out,result['manifest_sha256'],recovery.digest(out/recovery.REVIEW_FILE))
            # The exact prior generation remains separate review evidence.
            self.assertEqual(recovery.read(out/'recovery-evidence/six/original-products.json')['B|https://example.test/B']['first_seen_date'],'2026-11-06')

    def test_mutated_inputs_fail_before_output_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);plan=self.fixture(root)
            (root/'six/known-products.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'INPUT_CHECKSUM'):
                recovery.prepare(plan,root/'out')
            self.assertFalse((root/'out').exists())

    def test_conflicting_event_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);plan=self.fixture(root);p=recovery.read(plan)
            path=root/'seven/flash-history.json'
            recovery.write(path,{'six':{'original':'conflict'}})
            p['sources'][-1]['files_sha256']['flash-history.json']=recovery.digest(path);recovery.write(plan,p)
            with self.assertRaisesRegex(ValueError,'HISTORY_CONFLICT'):
                recovery.prepare(plan,root/'out')
            self.assertFalse((root/'out').exists())

    def test_scope_hash_and_observation_date_mismatches_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);plan=self.fixture(root);p=recovery.read(plan)
            p['scope']['sha256']='0'*64;recovery.write(plan,p)
            with self.assertRaisesRegex(ValueError,'SCOPE_CHECKSUM'):
                recovery.prepare(plan,root/'out')
            p['scope']['sha256']=recovery.digest(root/'scope.json')
            path=root/'seven/latest.json';latest=recovery.read(path);latest['observed_date']='2026-11-06';recovery.write(path,latest)
            p['sources'][-1]['files_sha256']['latest.json']=recovery.digest(path);recovery.write(plan,p)
            with self.assertRaisesRegex(ValueError,'CHECKSUM|PROVENANCE|DATE'):
                recovery.prepare(plan,root/'out')

    def test_review_or_output_mutation_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);plan=self.fixture(root);out=root/'out';r=recovery.prepare(plan,out);approved=recovery.digest(out/recovery.REVIEW_FILE)
            with self.assertRaisesRegex(ValueError,'LEASE'):
                recovery.verify_review(out,'0'*64,approved)
            (out/'coverage-state.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'INPUT_CHECKSUM'):
                recovery.verify_review(out,r['manifest_sha256'],approved)
            (out/recovery.REVIEW_FILE).write_text('{}')
            with self.assertRaisesRegex(ValueError,'REVIEW_CHECKSUM'):
                recovery.verify_review(out,r['manifest_sha256'],approved)

    def test_explicit_reviewed_restore_avoids_old_flash_and_does_not_mutate_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);plan=self.fixture(root);out=root/'review';r=recovery.prepare(plan,out);approved=recovery.digest(out/recovery.REVIEW_FILE)
            with patch.object(restore,'ROOT',root/'working'),patch.object(restore,'MIN_KNOWN_PRODUCTS',1),patch.object(restore,'try_flash',side_effect=AssertionError('network fallback')):
                self.assertEqual(restore.main(['--reviewed-snapshot',str(out),'--expected-manifest-sha',r['manifest_sha256'],'--expected-review-sha',approved]),0)
                self.assertEqual(len(read_pool(root/'working')),3)
                self.assertEqual(set(read_history(root/'working')),{'old','six','seven'})
            recovery.verify_review(out,r['manifest_sha256'],approved)

    def test_output_must_not_overwrite_or_nest_in_an_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);plan=self.fixture(root)
            with self.assertRaisesRegex(ValueError,'new directory'):
                recovery.prepare(plan,root/'six')
            with self.assertRaisesRegex(ValueError,'inside an input'):
                recovery.prepare(plan,root/'six/nested')

    def test_original_archive_and_extracted_state_must_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);plan=self.fixture(root);p=recovery.read(plan)
            archive=root/'six.zip'
            with zipfile.ZipFile(archive,'w') as z:
                for path in (root/'six').rglob('*'):
                    if path.is_file():z.write(path,path.relative_to(root/'six').as_posix())
            source=p['sources'][1];source.update({'archive':'six.zip','archive_sha256':'0'*64});recovery.write(plan,p)
            with self.assertRaisesRegex(ValueError,'ARCHIVE_CHECKSUM'):
                recovery.prepare(plan,root/'out')
            source['archive_sha256']=recovery.digest(archive)
            path=root/'six/known-products.json';rows=recovery.read(path);next(iter(rows.values()))['product_name']='different';recovery.write(path,rows)
            source['files_sha256']['known-products.json']=recovery.digest(path);recovery.write(plan,p)
            with self.assertRaisesRegex(ValueError,'ARCHIVE_CONTENT'):
                recovery.prepare(plan,root/'out')

    def test_noncounted_identity_review_originals_survive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);plan=self.fixture(root);p=recovery.read(plan)
            row={'reason':'BRAND_IDENTITY_CONFLICT','identity_key':'original','review_status':'RESOLVED','record':{'original_name':'retain'}}
            path=root/'six/cumulative-products/review-queue.json';recovery.write(path,{'records':[row]})
            p['sources'][1]['files_sha256']['cumulative-products/review-queue.json']=recovery.digest(path);recovery.write(plan,p)
            out=root/'out';result=recovery.prepare(plan,out)
            self.assertEqual(recovery.read(out/'cumulative-products/review-queue.json')['records'],[row])
            self.assertEqual(recovery.read(out/'cumulative-products/manifest.json')['identity_resolved_product_count'],1)
            self.assertEqual(result['product_count'],3)

    def test_private_local_paths_are_redacted_only_in_review_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);plan=self.fixture(root);p=recovery.read(plan);source=root/'seven'
            latest=recovery.read(source/'latest.json');latest['artifact_path']='/Users/private-user/cache/scan.json';recovery.write(source/'latest.json',latest)
            recovery.write(source/'feed.json',{'summary':latest,'candidates':[]})
            build_cumulative_product_shards(source)
            for name in p['sources'][-1]['files_sha256']:p['sources'][-1]['files_sha256'][name]=recovery.digest(source/name)
            recovery.write(plan,p);out=root/'out';r=recovery.prepare(plan,out)
            self.assertEqual(recovery.read(out/'latest.json')['artifact_path'],'local-review:scan.json')
            self.assertTrue(r['metadata_path_redactions'])
            self.assertEqual(recovery.read(source/'latest.json')['artifact_path'],'/Users/private-user/cache/scan.json')
            self.assertFalse(any('/Users/private-user/' in f.read_text() for f in out.rglob('*.json')))


if __name__=='__main__':unittest.main()
