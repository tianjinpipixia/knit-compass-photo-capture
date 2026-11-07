"""Lossless event history with bounded, checksummed Git blobs.

Legacy flat objects remain readable. Checkpoints write content-addressed parts
before atomically replacing the index, retaining every event key.
"""
import hashlib
import json
import os
import re
import tempfile

INDEX = 'flash-history.json'
DIRECTORY = 'flash-history'
FORMAT = 'KC_BRAND64_FLASH_HISTORY_INDEX'
MAX_PART_BYTES = 8 * 1024 * 1024
PART_PATH = re.compile(r'flash-history/[0-9a-f]{64}\.json\Z')


def encode(value):
    return (json.dumps(value, ensure_ascii=False, separators=(',', ':'))+'\n').encode('utf-8')


def atomic_write(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.'+path.name, dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as output:
            output.write(raw)
            output.flush()
            os.fsync(output.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def read_history(root):
    path = root/INDEX
    if not path.exists():
        return {}
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError('History must be an object')
    if value.get('format') != FORMAT:
        return value
    history, paths = {}, set()
    for part in value['parts']:
        relative = part['path']
        if not PART_PATH.fullmatch(relative) or relative in paths:
            raise ValueError('Invalid/duplicate history part path')
        paths.add(relative)
        raw = (root/relative).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != part['sha256'] or relative != f'{DIRECTORY}/{digest}.json':
            raise ValueError('History part checksum mismatch')
        rows = json.loads(raw)
        if not isinstance(rows, dict) or len(rows) != part['event_count']:
            raise ValueError('History part count mismatch')
        if history.keys() & rows.keys():
            raise ValueError('Duplicate history event')
        history.update(rows)
    if len(history) != value['event_count']:
        raise ValueError('History total count mismatch')
    return history


def history_files(root):
    """Validate before returning every path needed for Git/artifact recovery."""
    read_history(root)
    if not (root/INDEX).exists():
        return []
    value = json.loads((root/INDEX).read_bytes())
    return [INDEX, *[part['path'] for part in value['parts']]] if value.get('format') == FORMAT else [INDEX]


def write_history(root, history, max_part_bytes=MAX_PART_BYTES):
    if not isinstance(history, dict):
        raise ValueError('History must be an object')
    buckets, parts = {}, []
    for key, row in history.items():
        bucket = hashlib.sha256(key.encode('utf-8')).hexdigest()[:2]
        buckets.setdefault(bucket, {})[key] = row

    def write_part(rows):
        raw = encode(dict(sorted(rows.items())))
        if len(raw) > max_part_bytes:
            keys = sorted(rows)
            if len(keys) < 2:
                raise ValueError('One history event exceeds part byte limit')
            middle = len(keys)//2
            write_part({key: rows[key] for key in keys[:middle]})
            write_part({key: rows[key] for key in keys[middle:]})
            return
        digest = hashlib.sha256(raw).hexdigest()
        relative = f'{DIRECTORY}/{digest}.json'
        path = root/relative
        if not path.exists() or path.read_bytes() != raw:
            atomic_write(path, raw)
        parts.append({'path': relative, 'sha256': digest, 'event_count': len(rows), 'size_bytes': len(raw)})

    for bucket in sorted(buckets):
        write_part(buckets[bucket])
    index = {'format': FORMAT, 'schema_version': '1.0', 'event_count': len(history), 'parts': parts}
    atomic_write(root/INDEX, encode(index))
    # The new index is durable; only now remove unreferenced local parts.
    keep = {part['path'] for part in parts}
    for path in (root/DIRECTORY).glob('*.json'):
        relative = path.relative_to(root).as_posix()
        if PART_PATH.fullmatch(relative) and relative not in keep:
            path.unlink()
    return [INDEX, *sorted(keep)]
