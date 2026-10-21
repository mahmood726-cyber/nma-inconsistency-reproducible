"""Compare a fresh R refit (written by validate.R into WORK) with the archived R reference, fresh candidate captures and historical original outputs.

Usage (called by validate.R): python -B analysis/run_checks.py .validate-work
Exits nonzero on any mismatch; writes WORK/summary.json only when every gate passes.
"""
import math, os, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, read, dump, deep_compare, check_expected

PM_TAG = 'uncentered package QE'

def strip_timing(rec):
    rec = dict(rec); assert 'seconds' in rec, 'Reference record without timing field'; rec.pop('seconds'); return rec

def align_tag(fresh, archived):
    """The bundle's reference.R reused cached FE/DL records written before it began tagging every record with
    pm_reference; the tag only marks which PM oracle produced a record. A fresh FE/DL record (or a refused PM record)
    may carry the tag where the archived one lacks it; nothing else may differ, and a fitted PM record must always carry it."""
    if 'pm_reference' in fresh and 'pm_reference' not in archived:
        # Mirrors the bundle's cache rule: a PM record could be reused untagged only if it was a refusal (no PM fit).
        assert not archived['key'].endswith('::PM') or archived['status'] == 'refused', 'Archived fitted PM record without the PM-oracle tag: ' + archived['key']
        assert fresh['pm_reference'] == PM_TAG, 'Unexpected PM-oracle tag'
        fresh = dict(fresh); fresh.pop('pm_reference'); return fresh, 1
    return fresh, 0

def order_splits(rec):
    """netmeta's netsplit row order follows locale collation of treatment labels, which differs between R sessions with
    different collation settings. Split rows are keyed by their (lexically sorted, sign-converted) comparison name, and
    compare_archive.py matches them by that name, so order is not part of the reference. Names must be unique."""
    rec = dict(rec); moved = False
    for field in ('nodeSplit', 'split_exclusions'):
        rows = rec.get(field)
        if isinstance(rows, list):
            names = [r['comparison'] for r in rows]
            assert len(names) == len(set(names)), f'Duplicate split comparison in {field}'
            ordered = sorted(rows, key=lambda r: r['comparison']); moved |= ordered != rows; rec[field] = ordered
    return rec, moved

def reproduce_reference(work):
    shipped = sorted((ROOT / 'results/reference').glob('*.json')); fresh = sorted((work / 'reference').glob('*.json'))
    assert [p.name for p in shipped] == [p.name for p in fresh], 'Fresh reference file set differs from archived reference'
    exact = 0; worst = 0.0; tagged = 0; reordered = 0
    for a, b in zip(fresh, shipped):
        x, y = strip_timing(read(a)), strip_timing(read(b))
        x, t = align_tag(x, y); tagged += t
        exact += x == y
        seq = lambda r: [[s['comparison'] for s in r.get(f) or []] for f in ('nodeSplit', 'split_exclusions')]
        reordered += seq(x) != seq(y)
        x, y = order_splits(x)[0], order_splits(y)[0]
        worst = max(worst, deep_compare(x, y, a.name))
    for name in ['normal-reference.json', 'bus-reference.json']:
        x, y = read(work / name), read(ROOT / 'results' / name)
        worst = max(worst, deep_compare(x, y, name)); exact += x == y
    # The multi-arm native-versus-flattened fits are an illustrative diagnostic (README fault table), not a
    # comparison oracle; they are held to the paper's 1e-9 numerical tolerance rather than 1e-12.
    x, y = read(work / 'multiarm-diagnostic.json'), read(ROOT / 'results/multiarm-diagnostic.json')
    diag = deep_compare(x, y, 'multiarm-diagnostic.json', rtol=1e-9)
    n = len(shipped) + 2
    print(f'Reference reproduction: {n}/{n} fresh R records match the archived reference '
          f'({exact} exactly equal after removing timing; {tagged} FE/DL or refused records differ only by the pm_reference tag; '
          f'{reordered} list split rows in a different (collation) order and are compared by comparison name; '
          f'max scaled difference {worst:.3g}; tolerance 1e-12)', flush=True)
    print(f'Multi-arm diagnostic reproduction: 3 native-versus-flattened fits match (max scaled difference {diag:.3g}; tolerance 1e-9)', flush=True)
    return dict(records=n, exact=exact, tag_only=tagged, split_order_only=reordered, max_difference=worst, multiarm_max_difference=diag)

def compare(work, variant):
    r = subprocess.run([sys.executable, '-B', str(ROOT / 'analysis/compare_archive.py'), variant, str(work / 'reference'), str(work)],
                       capture_output=True, text=True, encoding='utf-8', env=dict(os.environ, PYTHONIOENCODING='utf-8'))
    (work / f'compare-{variant}.log').write_text(r.stdout + r.stderr, encoding='utf-8')
    assert r.returncode == 0, f'compare_archive.py {variant} failed: {r.stderr[-2000:]}'
    print(r.stdout, end='', flush=True)
    return read(work / f'results-{variant}.json')

def rescore_focused(variant, normal, bus, work=None):
    """Re-score R-oracle checks; use fresh candidate verdicts and historical original verdicts for other checks."""
    fresh_capture = variant == 'patched'
    assert not fresh_capture or work is not None, 'Candidate focused capture required'
    f = read(work / 'capture/focused-patched.json') if fresh_capture else read(ROOT / f'results/focused-{variant}.json')
    shipped_normal = normal if fresh_capture else read(ROOT / 'results/normal-reference.json')
    fixtures = {x['key']: x for x in bus}
    shipped_bus = fixtures if fresh_capture else {x['key']: x for x in read(ROOT / 'results/bus-reference.json')}
    finite = lambda v: isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
    normal_checks = [c for c in f['results'] if c['name'].startswith('normal_p::')]
    assert len(normal_checks) == len(normal) == len(shipped_normal), 'Normal-oracle check count'
    passed = 0; rescored = 0
    verdict = {}
    for c, fresh, old in zip(normal_checks, normal, shipped_normal):
        assert c['expected'] == old['p'], 'Archived focused expectation is not the archived R oracle'
        verdict[id(c)] = finite(c['got']) and abs(c['got'] - fresh['p']) <= 1e-9
    for c in f['results']:
        if not c['name'].startswith('bus_numeric::'):
            continue
        parts = c['name'].split('::'); key = parts[1] + '::' + parts[2]; fx = fixtures[key]; old = shipped_bus[key]
        if parts[3] == 'count':
            assert c['expected'] == len(old['rows']); verdict[id(c)] = c['got'] == len(fx['rows'])
        else:
            i, field = int(parts[3]), parts[4]; ref = fx['rows'][i][field]
            assert c['expected'] == old['rows'][i][field], 'Archived bus expectation is not the archived R fixture'
            verdict[id(c)] = c['got'] == ref if field in ('A', 'B') else (finite(c['got']) and abs(c['got'] - ref) <= 1e-9 * max(1, abs(ref)))
    for c in f['results']:
        ok = verdict.get(id(c), c['pass']); rescored += id(c) in verdict; passed += ok
    assert passed == f['passed'], f'Focused {variant}: {passed}/{len(f["results"])} after rescoring differs from archived {f["passed"]}'
    return dict(checks=len(f['results']), passed=passed, rescored_against_fresh_R=rescored)

def main():
    work = Path(sys.argv[1]).resolve(); expected = read(ROOT / 'expected/paper_values.json')
    rep = reproduce_reference(work)
    statuses = {}
    for p in sorted((work / 'reference').glob('*.json')):
        s = read(p)['status']; statuses[s] = statuses.get(s, 0) + 1
    assert statuses == expected['reference_statuses'], f'Fresh reference statuses {statuses} differ from expected'
    results = {}
    for v in ['original', 'patched']:
        results[v] = compare(work, v); check_expected(results[v], expected[v], 'fresh ' + v)
    normal, bus = read(work / 'normal-reference.json'), read(work / 'bus-reference.json')
    focused = {v: rescore_focused(v, normal, bus, work) for v in ['original', 'patched']}
    for v in ['original', 'patched']:
        e = expected['focused_' + v]; assert (focused[v]['passed'], focused[v]['checks']) == (e['passed'], e['checks']), 'Focused ' + v
    p = results['patched']; o = results['original']
    assert p['passed'] == p['checks'] and p['failed'] == 0, 'Patched comparison is not all-pass'
    lines = [f"Fresh R reference statuses: {statuses}",
             f"Original (historical page, expected failures): {o['passed']}/{o['checks']} checks pass - matches expected/paper_values.json",
             f"Focused original (archived Node observations; {focused['original']['rescored_against_fresh_R']} rescored against fresh R): {focused['original']['passed']}/{focused['original']['checks']} focused checks pass",
             f"Focused patched (fresh candidate Node observations; {focused['patched']['rescored_against_fresh_R']} rescored against fresh R): {focused['patched']['passed']}/{focused['patched']['checks']} focused checks pass",
             f"{p['passed']}/{p['checks']} checks pass"]
    for line in lines[:-1]:
        print(line, flush=True)
    dump(work / 'summary.json', dict(reference=rep, statuses=statuses, original=dict(checks=o['checks'], passed=o['passed']),
                                     patched=dict(checks=p['checks'], passed=p['passed']), focused=focused, final_line=lines[-1]))

if __name__ == '__main__':
    main()
