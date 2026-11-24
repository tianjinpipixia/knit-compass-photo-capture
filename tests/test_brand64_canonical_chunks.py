import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import brand64_canonical_chunks as chunks


class CanonicalChunkTests(unittest.TestCase):
    def test_large_source_is_preserved_exactly_in_bounded_utf8_fragments(self):
        # Cross the real reader ceiling, including multibyte text at boundaries.
        raw = (json.dumps({'records': [{'product_id': 'unchanged',
               'evidence': '糸' * 5_400_000}]}, ensure_ascii=False) + '\n').encode()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'cumulative-products/BR-00018.json'
            source.parent.mkdir()
            source.write_bytes(raw)
            brand = {'brand_id': 'BR-00018', 'path': 'cumulative-products/BR-00018.json',
                     'sha256': hashlib.sha256(raw).hexdigest()}
            generated = chunks.add_canonical_chunks(root, brand)
            self.assertGreater(len(generated), 1)
            contents = [(root / path).read_bytes() for path in generated]
            self.assertEqual(b''.join(contents), raw)
            self.assertEqual(source.read_bytes(), raw)  # existing readers still work
            for content, entry in zip(contents, brand['chunks']):
                content.decode('utf-8', errors='strict')
                self.assertLessEqual(len(content), 16_000_000)
                self.assertEqual(len(content), entry['bytes'])
                self.assertEqual(hashlib.sha256(content).hexdigest(), entry['sha256'])
            # A later small source must not retain old descriptors/fragments.
            source.write_bytes(b'{"records":[]}\n')
            brand['sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
            self.assertEqual(chunks.add_canonical_chunks(root, brand), [])
            self.assertNotIn('chunks', brand)
            self.assertEqual(list(source.parent.glob('*.part-*')), [])

    def test_bad_source_checksum_fails_before_any_transport_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'cumulative-products/BR-00018.json'
            source.parent.mkdir()
            source.write_bytes(b'{}')
            with self.assertRaisesRegex(ValueError, 'checksum'):
                chunks.add_canonical_chunks(root, {'brand_id': 'BR-00018',
                    'path': 'cumulative-products/BR-00018.json', 'sha256': '0' * 64})
            self.assertEqual(list(source.parent.glob('*.part-*')), [])


if __name__ == '__main__':
    unittest.main()
