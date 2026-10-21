"""Refresh the two archive inventories using the archive's hashing helpers.

Historical bundle, EOL, compression and upstream manifests are immutable.
The archive previously shipped inventory readers only; this entry point exposes
common.source_files/sha/dump for reproducible candidate re-cuts.
"""
from common import ROOT, dump, inventory, read, sha, source_files


def refresh():
    app = ROOT / 'app'
    paths = sorted(p for p in app.rglob('*') if p.is_file() and p.name != 'app-sha256.json')
    dump(app / 'app-sha256.json', {p.relative_to(app).as_posix(): sha(p) for p in paths})
    paths = source_files()
    dump(ROOT / 'SOURCE_SHA256.json', {p.relative_to(ROOT).as_posix(): sha(p) for p in paths})
    n = inventory(paths, ROOT, read(ROOT / 'SOURCE_SHA256.json'))
    print(f'INVENTORY PASS: {n} files; app/app-sha256.json and SOURCE_SHA256.json regenerated')


if __name__ == '__main__':
    refresh()
