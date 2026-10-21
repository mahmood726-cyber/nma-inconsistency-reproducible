"""Fail-closed archive verifier: inventory, bundle provenance, compression, patch replay, coverage, text hygiene, metadata.

Run from anywhere: python analysis/verify_archive.py   (no Git writes)
"""
import difflib, hashlib, json, sys
CR, LF, CRLF = bytes([13]), bytes([10]), bytes([13, 10])
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (ROOT, read, sha, source_files, inventory, clean_text, is_text, provenance_text, metadata, sizes,
                    compressed, check_expected, RELEASE, RELEASE_COMMIT, RELEASE_DOI)

CONFIG = {
    16: dict(title='Node-splitting and design-by-treatment inconsistency in the browser: validation against the R package netmeta',
             page='nma-inconsistency/index.html',
             bundle_excluded={'P16-validation.zip', 'archive-manifest.json', 'PROGRESS.md', 'RUN.json', 'codex.log'}),
    17: dict(title='Correlation meta-analysis in the browser: validation against the R package metafor',
             page='correlation-ma/index.html',
             bundle_excluded={'P17-validation.zip', 'archive-manifest.json', 'PROGRESS.md', 'RUN.json', 'codex.log', 'app.json'},
             bundle_excluded_prefix=('node_modules/',),
             # PowerShell Set-Content -Encoding UTF8 (bench/run_r.ps1) wrote this bundle log with a BOM; kept byte-identical.
             bom_allowed={'bench/reference.log'}),
}
PAPER = read(ROOT / 'expected/paper_values.json')['paper']
CFG = CONFIG[PAPER]

def bundle_name(rel, proof):
    """Map an archive path to the path it had in the extracted validation bundle (None for files authored here)."""
    parts = rel.split('/')
    if rel in proof:
        return proof[rel]['original_name']
    if parts[0] == 'app' and len(parts) > 2 and parts[1] in ('original', 'historical-patched'):
        variant = 'patched' if parts[1] == 'historical-patched' else 'original'
        return f'app-{variant}/' + '/'.join(parts[2:])
    if rel in ('app/source-manifest.json', 'app/LICENSE.app.txt'):
        return parts[-1]
    if parts[0] in ('data', 'results') and rel != 'data/bundle-provenance.json':
        return '/'.join(parts[1:])
    if parts[0] == 'bench':
        if rel == 'bench/bundle-README.md':
            return 'README.md'
        if rel == 'bench/bundle-archive-manifest.json':
            return None
        return '/'.join(parts[1:])
    return None

def bundle_manifest():
    m = read(ROOT / 'bench/bundle-archive-manifest.json')
    if isinstance(m, list):
        return {x['file']: x['sha256'] for x in m}
    return {k: v['sha256'] for k, v in m.items()}

def eol_record():
    return read(ROOT / 'analysis/eol_normalization.json')

def bundle_digest(p, rel, proof, eol):
    """SHA-256 of the file as it was in the bundle: the xz original, the CRLF form of a normalized file, or the bytes as stored."""
    rel = rel.replace('app/historical-patched/', 'app/patched/')
    if rel in proof:
        return proof[rel]['original_sha256']
    raw = Path(p).read_bytes()
    if rel in eol:
        assert CR not in raw, 'EOL-normalized file still contains CR: ' + rel
        crlf = raw.replace(LF, CRLF); assert hashlib.sha256(crlf).hexdigest() == eol[rel], 'EOL-normalized file changed: ' + rel
        return eol[rel]
    return hashlib.sha256(raw).hexdigest()

def provenance_against_bundle():
    proof = {r['stored']: r for r in read(ROOT / 'analysis/compression_proof.json')}
    eol = eol_record()
    manifest = bundle_manifest(); matched = set(); authored = []
    for p in source_files():
        rel = p.relative_to(ROOT).as_posix(); name = bundle_name(rel, proof)
        if name is None:
            authored.append(rel); continue
        if name not in manifest:
            # Files produced by the bundle's own final archive step are not listed in its manifest.
            assert name in ('verification.json',), 'Bundle file absent from bundle manifest: ' + rel
            authored.append(rel); continue
        digest = bundle_digest(p, rel, proof, eol)
        assert digest == manifest[name], 'Archive file differs from the validation bundle: ' + rel
        matched.add(name)
    missing = sorted(n for n in set(manifest) - matched
                     if n not in CFG['bundle_excluded'] and not n.startswith(CFG.get('bundle_excluded_prefix', ('\0',))))
    assert not missing, f'Bundle files neither archived nor documented as excluded: {missing[:5]}'
    return len(matched), authored

def app_sources():
    app = ROOT / 'app'
    inventory([p for p in app.rglob('*') if p.is_file() and p.name != 'app-sha256.json'], app, read(app / 'app-sha256.json'))
    m = read(app / 'source-manifest.json')
    rows = m['files'].items() if isinstance(m['files'], dict) else [(x['file'], x['sha256']) for x in m['files']]
    rows = list(rows); assert rows, 'Empty upstream source manifest'
    eol = eol_record()
    for rel, digest in rows:
        assert bundle_digest(app / 'original' / rel, 'app/original/' + rel, {}, eol) == digest, 'Original page asset differs from upstream manifest: ' + rel
    assert m['commit'] == '7966530de875d22253f0557c7b447ed9d917685d', 'Unexpected source commit'
    assert (app / 'original' / CFG['page']).is_file() and (app / 'patched' / CFG['page']).is_file(), 'Missing page snapshot'
    return len(rows)

def patch_replay(patched=None):
    """Reconstruct bench/make_patch.py's exact diff, without any Git writes.

    Exact patch equality and equality of every unchanged file prove the
    historical transformation. No fuzz, offset or whitespace tolerance.
    """
    patched = Path(patched) if patched else ROOT / 'app/historical-patched'
    original = ROOT / 'app/original'
    a = {p.relative_to(original).as_posix(): p.read_bytes() for p in original.rglob('*') if p.is_file()}
    b = {p.relative_to(patched).as_posix(): p.read_bytes() for p in patched.rglob('*') if p.is_file()}
    assert set(a) == set(b), 'Historical patch file set differs'
    changed = ['nma-inconsistency/index.html', 'nma-inconsistency/README.md']
    assert all(a[k] == b[k] for k in a if k not in changed), 'Historical unpatched asset changed'
    diff = ''
    for rel in changed:
        assert CR not in a[rel] and CR not in b[rel], 'Historical patch inputs must be LF'
        diff += ''.join(difflib.unified_diff(a[rel].decode('utf-8').splitlines(True),
                       b[rel].decode('utf-8').splitlines(True), fromfile='a/' + rel, tofile='b/' + rel))
    assert diff.encode('utf-8') == (ROOT / 'bench/fix.patch').read_bytes(), 'Historical fix.patch reconstruction differs'
    return len(b)

def candidate_sources(patched=None):
    patched = Path(patched) if patched else ROOT / 'app/patched'
    m = read(ROOT / 'app/candidate-source.json')
    assert m['commit'] == RELEASE_COMMIT and m['release'] == RELEASE and m['release_doi'] == RELEASE_DOI, 'Unexpected release commit'
    raw = {p.relative_to(patched).as_posix(): p.read_bytes() for p in patched.rglob('*') if p.is_file()}
    got = {rel: hashlib.sha256(b.replace(CRLF, LF)).hexdigest() for rel, b in raw.items()}
    assert got == m['files'], 'Candidate source mismatch'
    # Release snapshot: exact committed bytes, so every file must also equal its v1.8.0 Git blob.
    assert {rel: git_blob(b) for rel, b in raw.items()} == m['git_blobs'], 'Snapshot differs from the v1.8.0 Git blobs'
    plus = read(ROOT / 'plus/app/SOURCE.json')
    assert plus['commit'] == RELEASE_COMMIT, 'Unexpected plus source commit'
    for row in plus['files']:
        b = (ROOT / 'plus/app' / row['path']).read_bytes()
        assert hashlib.sha256(b).hexdigest() == row['sha256'] and git_blob(b) == row['git_blob'], 'Plus source mismatch'
    return len(got)

def git_blob(b):
    return hashlib.sha1(b'blob ' + str(len(b)).encode() + bytes([0]) + b).hexdigest()

def release_equivalence():
    eq = (ROOT / 'RELEASE_EQUIVALENCE.md').read_text(encoding='utf-8')
    for needle in [RELEASE_COMMIT, 'byte-identical', 'PLUS NODE REPLAY 643413/643413', '76601/76601', '319/319',
                   '42/42', 'plus/evidence/browser-v180/', '1f5ce9e', 'clears results']:
        assert needle in eq, 'Release equivalence record missing: ' + needle

def browser_v180(d=None):
    """The plus browser tier re-run on the v1.8.0 bytes must match its expected record; the older run stays as history."""
    d = Path(d) if d else ROOT / 'plus/evidence/browser-v180'
    exp = read(d / 'expected-browser.json')
    assert exp['release'] == RELEASE and exp['commit'] == RELEASE_COMMIT, 'Browser record release'
    log = (d / 'pw-gates-v180.log').read_text(encoding='utf-8').splitlines()
    tests = [l.split('] ', 1)[1] for l in log if l.startswith('[') and '/42] ' in l[:8]]
    assert tests == exp['tests'] and len(tests) == 42, 'Browser test list'
    assert any(l.startswith(f'  {exp["summary"]} (') for l in log), 'Browser summary'
    assert exp['summary'] == '42 passed' and 'exit=0' in log and not any(' failed' in l or ' skipped' in l or ' flaky' in l for l in log), 'Browser run not all-pass'
    for k in ['plus_replay', 'tampered_plus_replay', 'fig2']:
        assert exp[k] in log, 'Browser log line: ' + k
    assert exp['plus_replay'].startswith('plus replay 643413/643413 ') and exp['tampered_plus_replay'].startswith('tampered plus replay 643412/643413 ')
    assert '155.0.4283.62' in exp['fig2'] and exp['browser'] == 'Microsoft Edge 155.0.4283.62', 'Browser version'
    walk = [l for l in log if l.startswith('WALKTHROUGH ')]
    assert len(walk) == 1 and json.loads(walk[0][12:]) == exp['walkthrough'] == read(d / 'shots/walkthrough-result.json'), 'Walkthrough record'
    assert exp['walkthrough']['axeFullPage']['violations'] == [], 'axe violations'
    assert read(d / 'shots/fig2-capture.json')['browser'] == '155.0.4283.62', 'Figure 2 browser'
    # v1.8.0 behaviour (allmeta 1f5ce9e): invalid input clears results; the superseded "keeps results" test must not be claimed.
    usab = [t for t in tests if 'nma-inconsistency-usability.spec.mjs:37:1' in t]
    assert usab == [exp['superseded']['usability_test']['v1.8.0']] and usab[0].endswith('invalid input explains and clears results'), 'Usability behaviour'
    assert not any('keeps results' in t for t in tests), 'Superseded usability test in v1.8.0 run'
    old = (ROOT / exp['superseded']['log']).read_text(encoding='utf-8')
    assert exp['superseded']['usability_test']['before'] in old and 'keeps results' in exp['superseded']['usability_test']['before'], 'Superseded record'
    spec = (ROOT / 'plus/app/hub/shared/tests/nma-inconsistency-usability.spec.mjs').read_text(encoding='utf-8')
    assert 'invalid input explains and clears results' in spec and 'keeps results' not in spec, 'Usability spec is not the v1.8.0 one'
    site = read(d / 'runner/site-manifest.json')
    assert site['commit'] == RELEASE_COMMIT and len(site['files']) == 49, 'Browser site manifest'
    for row in site['files']:
        if row['source'].startswith(('plus/app/', 'app/patched/')):
            b = (ROOT / row['source']).read_bytes()
            assert hashlib.sha256(b).hexdigest() == row['sha256'] and git_blob(b) == row['git_blob'], 'Browser site file: ' + row['path']
    return len(tests)

def coverage():
    if PAPER == 16:
        keys = [c['key'] for c in read(ROOT / 'data/corpus.json')]
        refs = [read(p)['key'] for p in sorted((ROOT / 'results/reference').glob('*.json'))]
        sets = dict(reference=refs, original=[a['key'] for a in read(ROOT / 'results/app-original.json.xz')],
                    patched=[a['key'] for a in read(ROOT / 'results/app-patched.json.xz')])
    else:
        keys = [f"{c['id']}::{m}" for c in read(ROOT / 'data/corpus.json') for m in ['REML', 'PM', 'DL', 'FE']]
        sets = dict(reference=[r['id'] for r in read(ROOT / 'results/reference.json')],
                    original=[a['id'] for a in read(ROOT / 'results/app-original.json')],
                    patched=[a['id'] for a in read(ROOT / 'results/app-patched.json')])
    expected = read(ROOT / 'expected/paper_values.json')
    assert len(keys) == len(set(keys)) == expected['configurations'], 'Corpus key coverage'
    for name, ks in sets.items():
        assert len(ks) == len(set(ks)) and set(ks) == set(keys), 'Keyed coverage: ' + name
    for v in ['original', 'patched']:
        check_expected(read(ROOT / f'results/results-{v}.json'), expected[v], 'archived ' + v)
    assert expected['patched']['passed'] == expected['patched']['checks'], 'Patched archive must be all-pass'
    if PAPER == 16:
        for v in ['original', 'patched']:
            f = read(ROOT / f'results/focused-{v}.json'); e = expected['focused_' + v]
            assert (f['passed'], f['checks']) == (e['passed'], e['checks']) == (sum(x['pass'] for x in f['results']), len(f['results'])), 'Focused counts'
    return len(keys)

def verify():
    files = source_files()
    n = inventory(files, ROOT, read(ROOT / 'SOURCE_SHA256.json'))
    sizes([p.stat().st_size for p in files + [ROOT / 'SOURCE_SHA256.json']])
    proof = read(ROOT / 'analysis/compression_proof.json')
    assert {r['stored'] for r in proof} == {p.relative_to(ROOT).as_posix() for p in files if p.suffix == '.xz'}, 'Compression inventory'
    for r in proof:
        compressed(ROOT / r['stored'], r)
    eol = eol_record()
    assert all((ROOT / rel).is_file() for rel in eol), 'EOL record lists a missing file'
    for p in files + [ROOT / 'SOURCE_SHA256.json']:
        if is_text(p):
            rel, raw = p.relative_to(ROOT).as_posix(), p.read_bytes()
            if rel in CFG.get('bom_allowed', ()) and raw.startswith(bytes([0xEF, 0xBB, 0xBF])):
                raw = raw[3:]
            clean_text(raw, rel)
    for name in ['README.md', 'CITATION.cff', '.zenodo.json']:
        provenance_text((ROOT / name).read_text(encoding='utf-8'), name)
    metadata(read(ROOT / '.zenodo.json'), CFG['title'])
    matched, authored = provenance_against_bundle()
    upstream = app_sources(); replay = patch_replay(); candidate = candidate_sources(); keys = coverage(); release_equivalence()
    browser = browser_v180()
    plus = len(read(ROOT / 'plus/app/SOURCE.json')['files'])
    print(f'ARCHIVE PASS: {n} pinned files; {matched} identical to the validation-bundle manifest ({len(eol_record())} via reversible CRLF-to-LF normalization); {len(authored)} archive-authored; '
          f'{upstream} original assets match upstream {read(ROOT / "app/source-manifest.json")["commit"][:7]}; fix.patch reconstruction matches {replay} historical patched files; '
          f'{candidate}/{candidate} snapshot files match allmeta {RELEASE} ({RELEASE_COMMIT[:7]}) blobs; {plus}/{plus} plus files match {RELEASE} blobs; plus browser tier {browser}/{browser} passed on {RELEASE} bytes; '
          f'{keys} configurations with exact keyed coverage; release {RELEASE}, DOI {RELEASE_DOI}; RELEASE_EQUIVALENCE.md present', flush=True)

if __name__ == '__main__':
    verify()
