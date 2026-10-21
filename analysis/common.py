"""Shared fail-closed helpers for the archive gates (standard library only)."""
import hashlib, json, lzma, math, os, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDE_DIRS = {'.git', '__pycache__', '.pytest_cache', '.validate-work'}
UNPINNED = {'SOURCE_SHA256.json'}
TEXT_SUFFIXES = {'.py', '.r', '.js', '.cjs', '.mjs', '.json', '.md', '.html', '.txt', '.csv', '.cff', '.css', '.patch', '.diff', '.log', '.ps1', '.svg', ''}
RELEASE_TOKENS = {'ALLMETA_RELEASE', 'ALLMETA_RELEASE_DOI'}
PENDING = 'the next allmeta release (pending)'
RELEASE, RELEASE_COMMIT, RELEASE_DOI = 'v1.8.0', '1cb3f8409c7af75ed41f7e1811f9c502f900fc79', '10.5281/zenodo.23515177'
RELEASE_URL = 'https://github.com/mahmood726-cyber/allmeta/releases/tag/v1.8.0'
MACHINE_PATH = [re.compile(r'\b[A-Za-z]:[\\/]+(?:Users|Projects|claude-temp|claude|Program Files|Windows)\b', re.I),
                re.compile(r'(?<![\w.])/(?:c|d|f)/(?:Users|Projects|f1000)', re.I),
                re.compile(r'(?<![\w.])/(?:home|Users|mnt/[cdf])/[A-Za-z0-9_.-]+/')]
SECRET = [re.compile(r'gh[pousr]_[A-Za-z0-9]{30,}'), re.compile(r'sk-[A-Za-z0-9_-]{20,}'), re.compile(r'AKIA[0-9A-Z]{16}'),
          re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----'), re.compile(r'xox[baprs]-[A-Za-z0-9-]{10,}')]

def read(p):
    p = Path(p)
    raw = p.read_bytes()
    if p.suffix == '.xz':
        raw = lzma.decompress(raw)
    return json.loads(raw.decode('utf-8'))

def dump(p, obj):
    Path(p).write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n', encoding='utf-8', newline='\n')

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def source_files(root=ROOT):
    out = []
    for directory, dirs, names in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith('.verify-'))
        rel = Path(directory).relative_to(root)
        out.extend(Path(directory) / n for n in names if not (rel == Path('.') and n in UNPINNED))
    return sorted(out)

def inventory(paths, base, pins):
    got = {p.relative_to(base).as_posix(): sha(p) for p in paths}
    missing = sorted(set(pins) - set(got)); extra = sorted(set(got) - set(pins))
    changed = sorted(k for k in set(got) & set(pins) if got[k] != pins[k])
    assert not (missing or extra or changed), f'Inventory/hash mismatch: missing={missing[:3]} extra={extra[:3]} changed={changed[:3]}'
    return len(got)

def clean_text(raw, name='text'):
    assert not raw.startswith(b'\xef\xbb\xbf'), 'UTF-8 BOM: ' + name
    text = raw.decode('utf-8')
    for pattern in MACHINE_PATH:
        m = pattern.search(text)
        assert not m, f'Machine path in {name}: {m.group(0)!r}'
    for pattern in SECRET:
        assert not pattern.search(text), 'Secret-like token in ' + name
    return text

def is_text(p):
    return p.suffix.lower() in TEXT_SUFFIXES and p.suffix.lower() != '.xz'

def provenance_text(text, name='provenance'):
    """Filled-release state: no placeholder or other angle-bracketed token, no pending wording, the v1.8.0 tag, commit and DOI present."""
    tokens = set(re.findall(r'<([^<>\s]+)>', text))
    assert not tokens, f'Unexpected or unfilled provenance placeholder in {name}: {sorted(tokens)}'
    assert '<ALLMETA_RELEASE' not in text, 'Unfilled release token: ' + name
    assert PENDING not in text and 'pending' not in text.lower(), 'Pending-release wording remains: ' + name
    assert RELEASE in text and RELEASE_COMMIT in text and RELEASE_DOI in text, 'allmeta v1.8.0 tag/commit/DOI missing: ' + name
    assert set(re.findall(r'10\.5281/zenodo\.\d+', text)) == {RELEASE_DOI}, 'Unexpected DOI asserted: ' + name

def metadata(z, title):
    assert z['title'] == title, 'Zenodo title'
    assert z['creators'] == [{'name': 'Ahmad, Mahmood'}], 'Zenodo creators'
    assert z['license'] == 'MIT' and z['version'] == '1.0.0' and z['upload_type'] == 'software' and z['access_right'] == 'open', 'Zenodo fields'
    assert z['related_identifiers'] == [
        dict(identifier='https://github.com/mahmood726-cyber/allmeta', relation='isDerivedFrom', scheme='url'),
        dict(identifier=RELEASE_URL, relation='isDerivedFrom', scheme='url'),
        dict(identifier=RELEASE_DOI, relation='isDerivedFrom', scheme='doi')], 'Zenodo related identifiers'

def sizes(values):
    assert values and max(values) < 90_000_000 and sum(values) < 500_000_000, 'Archive size limit'

def compressed(p, record):
    raw = Path(p).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == record['stored_sha256'], 'Compressed hash: ' + str(p)
    assert hashlib.sha256(lzma.decompress(raw)).hexdigest() == record['original_sha256'], 'Decoded hash: ' + str(p)

def deep_compare(a, b, path='$', rtol=1e-12, stats=None):
    """Structure, strings, booleans and integers exact; floats within rtol*max(1,|b|). Returns max scaled difference."""
    if stats is None:
        stats = dict(max=0.0)
    if isinstance(b, dict):
        assert isinstance(a, dict) and sorted(a) == sorted(b), f'Keys differ at {path}'
        for k in b:
            deep_compare(a[k], b[k], f'{path}.{k}', rtol, stats)
    elif isinstance(b, list):
        assert isinstance(a, list) and len(a) == len(b), f'Length differs at {path}'
        for i, (x, y) in enumerate(zip(a, b)):
            deep_compare(x, y, f'{path}[{i}]', rtol, stats)
    elif isinstance(b, bool) or b is None or isinstance(b, str):
        assert type(a) is type(b) and a == b, f'Value differs at {path}: {a!r} vs {b!r}'
    elif isinstance(b, (int, float)):
        assert isinstance(a, (int, float)) and not isinstance(a, bool), f'Type differs at {path}'
        if isinstance(a, int) and isinstance(b, int):
            assert a == b, f'Integer differs at {path}: {a} vs {b}'
        else:
            assert math.isfinite(a) and math.isfinite(b), f'Nonfinite at {path}'
            d = abs(a - b) / max(1.0, abs(b))
            stats['max'] = max(stats['max'], d)
            assert d <= rtol, f'Numeric difference at {path}: {a!r} vs {b!r} ({d:.3g} > {rtol:g})'
    else:
        raise AssertionError(f'Unsupported type at {path}')
    return stats['max']

def check_expected(result, expected, label):
    """Totals and every per-quantity count must equal the pinned paper values exactly."""
    total = result.get('checks', result.get('total'))
    assert total == expected['checks'] and result['passed'] == expected['passed'], \
        f'{label}: {result["passed"]}/{total} differs from expected {expected["passed"]}/{expected["checks"]}'
    got = {q: dict(checks=s['checks'], passed=s['passed']) for q, s in result['quantities'].items()}
    assert got == expected['quantities'], f'{label}: per-quantity counts differ from expected/paper_values.json'
    assert sum(s['checks'] for s in got.values()) == total and sum(s['passed'] for s in got.values()) == result['passed'], label + ': totals'
