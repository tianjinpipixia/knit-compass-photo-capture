"""Optional transport fragments; the canonical file and its checksum stay intact."""
import hashlib
from pathlib import Path

READER_LIMIT_BYTES = 16_000_000
CHUNK_BYTES = 8_000_000


def add_canonical_chunks(root: Path, brand: dict) -> list[str]:
    relative = brand['path']
    if relative != f"cumulative-products/{brand['brand_id']}.json":
        raise ValueError('Invalid canonical chunk source path')
    source = root / relative
    raw = source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != brand['sha256']:
        raise ValueError('Canonical chunk source checksum mismatch')
    # Keep the full source for existing readers. Never regenerate product facts.
    raw.decode('utf-8', errors='strict')
    for old in source.parent.glob(source.name + '.part-*'):
        old.unlink()
    brand.pop('chunks', None)
    if len(raw) <= READER_LIMIT_BYTES:
        return []
    chunks = []
    start = 0
    while start < len(raw):
        end = min(start + CHUNK_BYTES, len(raw))
        # Each fragment is valid UTF-8, even when the boundary crosses Japanese.
        while end < len(raw) and raw[end] & 0xC0 == 0x80:
            end -= 1
        content = raw[start:end]
        path = f'{relative}.part-{len(chunks) + 1:04d}'
        (root / path).write_bytes(content)
        chunks.append({'path': path, 'bytes': len(content),
                       'sha256': hashlib.sha256(content).hexdigest()})
        start = end
    brand['chunks'] = chunks
    return [chunk['path'] for chunk in chunks]
