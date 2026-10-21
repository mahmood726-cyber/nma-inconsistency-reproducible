"""Negative tests: every archive gate must reject a planted defect. Fixtures here are tests, not research output.

Run: python analysis/test_safeguards.py   (the version test also needs Rscript on PATH or RSCRIPT set)
"""
import copy, hashlib, lzma, os, shutil, subprocess, sys, unittest, uuid
from contextlib import contextmanager
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (ROOT, read, sha, inventory, clean_text, provenance_text, metadata, sizes, compressed, deep_compare,
                    check_expected, source_files)
import verify_archive as va

@contextmanager
def scratch_directory():
    # Inherit workspace permissions. Python 3.13's Windows mode-0700 temporary
    # directories deny the sandbox identity access to its own test fixtures.
    path = ROOT / ('.verify-safeguards-' + uuid.uuid4().hex)
    path.mkdir()
    try:
        yield str(path)
    finally:
        assert path.resolve().parent == ROOT.resolve() and not path.is_symlink()
        shutil.rmtree(path)


class Safeguards(unittest.TestCase):
    def rejects(self, fn, *args):
        with self.assertRaises((AssertionError, KeyError, ValueError, lzma.LZMAError)):
            fn(*args)

    def test_inventory(self):
        with scratch_directory() as d:
            p = Path(d) / 'x'; p.write_bytes(b'x'); pins = {'x': sha(p)}; inventory([p], Path(d), pins)
            self.rejects(inventory, [], Path(d), pins); self.rejects(inventory, [p], Path(d), {})
            self.rejects(inventory, [p], Path(d), dict(pins, y='0' * 64))
            p.write_bytes(b'y'); self.rejects(inventory, [p], Path(d), pins)

    def test_pinned_inventory_is_complete(self):
        pins = read(ROOT / 'SOURCE_SHA256.json')
        self.assertEqual(set(pins), {p.relative_to(ROOT).as_posix() for p in source_files()})

    def test_text_hygiene(self):
        clean_text(b'portable text')
        for bad in [b'\xef\xbb\xbftext', ('C' + ':\\' + 'Users' + '\\someone\\file').encode(), ('C' + ':/' + 'Users' + '/x').encode(),
                    ('/' + 'c/' + 'Users/x').encode(), ('/' + 'home/' + 'someone/x').encode(), ('gh' + 'p_' + 'a' * 36).encode(),
                    ('-----BEGIN ' + 'OPENSSH PRIVATE KEY-----').encode()]:
            self.rejects(clean_text, bad)

    def test_provenance_placeholders(self):
        for name in ['README.md', 'CITATION.cff', '.zenodo.json']:
            text = (ROOT / name).read_text(encoding='utf-8'); provenance_text(text, name)
            self.rejects(provenance_text, text + ' <' + 'ALLMETA_RELEASE' + '>')
            self.rejects(provenance_text, text + ' <' + 'ALLMETA_RELEASE_DOI' + '>')
            self.rejects(provenance_text, text + ' <' + 'ALLMETA_UNKNOWN' + '>')
            self.rejects(provenance_text, text + ' 10.5281/zenodo.12345678')
            self.rejects(provenance_text, text + ' the next allmeta release (pending)')
            self.rejects(provenance_text, text.replace('10.5281/zenodo.23515177', 'x'))
            self.rejects(provenance_text, text.replace('1cb3f8409c7af75ed41f7e1811f9c502f900fc79', 'x'))
            self.rejects(provenance_text, text.replace('v1.8.0', 'x'))

    def test_zenodo_metadata(self):
        z = read(ROOT / '.zenodo.json'); metadata(z, va.CFG['title'])
        for field, value in [('title', 'wrong'), ('creators', [{'name': 'Someone, Else'}]), ('creators', []), ('version', '2.0.0'),
                             ('license', 'other'), ('related_identifiers', [])]:
            zz = copy.deepcopy(z); zz[field] = value; self.rejects(metadata, zz, va.CFG['title'])

    def test_sizes(self):
        sizes([1]); self.rejects(sizes, [90_000_000]); self.rejects(sizes, [80_000_000] * 7); self.rejects(sizes, [])

    def test_compression(self):
        with scratch_directory() as d:
            p = Path(d) / 'x.xz'; p.write_bytes(lzma.compress(b'x'))
            r = dict(stored_sha256=sha(p), original_sha256=hashlib.sha256(b'x').hexdigest()); compressed(p, r)
            self.rejects(compressed, p, dict(r, original_sha256='0' * 64)); p.write_bytes(b'bad'); self.rejects(compressed, p, r)

    def test_reference_comparator(self):
        a = {'k': 'x', 'n': 3, 'v': [1.0, 2.5e-7], 'p': None, 'ok': True}
        deep_compare(copy.deepcopy(a), a)
        for mutate in [lambda b: b.update(k='y'), lambda b: b.update(n=4), lambda b: b['v'].__setitem__(0, 1.0 + 1e-10),
                       lambda b: b['v'].append(1.0), lambda b: b.pop('p'), lambda b: b.update(p=0.0), lambda b: b.update(ok=1),
                       lambda b: b['v'].__setitem__(1, float('nan'))]:
            b = copy.deepcopy(a); mutate(b); self.rejects(deep_compare, b, a)

    def test_expected_count_gate(self):
        e = read(ROOT / 'expected/paper_values.json')
        for v in ['original', 'patched']:
            r = read(ROOT / f'results/results-{v}.json'); check_expected(r, e[v], v)
            total = 'checks' if 'checks' in r else 'total'
            for mutate in [lambda x: x.update(passed=x['passed'] - 1), lambda x: x.update({total: x[total] + 1}),
                           lambda x: x['quantities'].pop(next(iter(x['quantities']))),
                           lambda x: x['quantities'][next(iter(x['quantities']))].update(passed=-1)]:
                x = copy.deepcopy(r); mutate(x); self.rejects(check_expected, x, e[v], v)

    def test_bundle_mapping(self):
        proof = {r['stored']: r for r in read(ROOT / 'analysis/compression_proof.json')}
        self.assertEqual(va.bundle_name('app/original/' + va.CFG['page'], proof), 'app-original/' + va.CFG['page'])
        self.assertEqual(va.bundle_name('bench/fix.patch', proof), 'fix.patch')
        self.assertIsNone(va.bundle_name('README.md', proof)); self.assertIsNone(va.bundle_name('data/bundle-provenance.json', proof))

    def test_patch_replay_detects_drift(self):
        va.patch_replay()
        with scratch_directory() as d:
            copy_dir = Path(d) / 'patched'; shutil.copytree(ROOT / 'app/historical-patched', copy_dir); va.patch_replay(copy_dir)
            page = copy_dir / va.CFG['page']; page.write_bytes(page.read_bytes() + b'<!-- drift -->'); self.rejects(va.patch_replay, copy_dir)
            page.unlink(); self.rejects(va.patch_replay, copy_dir)

    def test_candidate_sources_detect_drift(self):
        va.candidate_sources()
        with scratch_directory() as d:
            copy_dir = Path(d) / 'patched'; shutil.copytree(ROOT / 'app/patched', copy_dir)
            va.candidate_sources(copy_dir)
            page = copy_dir / va.CFG['page']; raw = page.read_bytes()
            page.write_bytes(bytes([raw[0] ^ 1]) + raw[1:])
            self.rejects(va.candidate_sources, copy_dir)
            page.write_bytes(raw); page.unlink()
            self.rejects(va.candidate_sources, copy_dir)

    def test_browser_v180_detects_drift(self):
        self.assertEqual(va.browser_v180(), 42)
        log_edits = [('invalid input explains and clears results', 'invalid input explains and keeps results'),
                     ('  42 passed (', '  1 failed\n  41 passed ('), ('exit=0', 'exit=1'),
                     ('plus replay 643413/643413 ', 'plus replay 643412/643413 '), ('"passes":29', '"passes":28')]
        for name, old, new in [('pw-gates-v180.log', a, b) for a, b in log_edits] + [
                ('shots/walkthrough-result.json', '"totalClicks": 3', '"totalClicks": 4'),
                ('shots/fig2-capture.json', '155.0.4283.62', '154.0.0.0'),
                ('expected-browser.json', '"summary": "42 passed"', '"summary": "41 passed"'),
                ('runner/site-manifest.json', '"source": "plus/app/nma-inconsistency/plus-ui.js",\n   "sha256": "5', '"source": "plus/app/nma-inconsistency/plus-ui.js",\n   "sha256": "0')]:
            with scratch_directory() as d:
                copy_dir = Path(d) / 'browser-v180'; shutil.copytree(ROOT / 'plus/evidence/browser-v180', copy_dir)
                va.browser_v180(copy_dir)
                p = copy_dir / name; text = p.read_text(encoding='utf-8')
                self.assertIn(old, text, name); p.write_text(text.replace(old, new, 1), encoding='utf-8', newline='\n')
                self.rejects(va.browser_v180, copy_dir)

    def test_eol_record(self):
        eol = va.eol_record(); rel = next(iter(eol)); p = ROOT / rel
        self.assertEqual(va.bundle_digest(p, rel, {}, eol), eol[rel])
        with scratch_directory() as d:
            q = Path(d) / 'x'; raw = p.read_bytes()
            q.write_bytes(raw.replace(va.LF, va.CRLF)); self.rejects(va.bundle_digest, q, rel, {}, eol)
            q.write_bytes(raw + b'x'); self.rejects(va.bundle_digest, q, rel, {}, eol)

    def test_pm_tag_alignment(self):
        if va.PAPER != 16:
            self.skipTest('pm_reference tag exists only in the netmeta reference')
        import run_checks as rc
        fresh = {'key': 'x::FE', 'pm_reference': rc.PM_TAG, 'v': 1.0}; arch = {'key': 'x::FE', 'v': 1.0}
        x, n = rc.align_tag(fresh, arch); deep_compare(x, arch); self.assertEqual(n, 1)
        self.rejects(rc.align_tag, dict(fresh, key='x::PM'), dict(arch, key='x::PM', status='ok'))
        self.assertEqual(rc.align_tag(dict(fresh, key='x::PM'), dict(arch, key='x::PM', status='refused'))[1], 1)
        self.rejects(rc.align_tag, dict(fresh, pm_reference='centered rma'), arch)
        x, _ = rc.align_tag(dict(fresh, v=2.0), arch); self.rejects(deep_compare, x, arch)

    def test_split_order_alignment(self):
        if va.PAPER != 16:
            self.skipTest('netsplit rows exist only in the netmeta reference')
        import run_checks as rc
        a = {'nodeSplit': [{'comparison': 'A vs B', 'diff': 1.0}, {'comparison': 'A vs C', 'diff': 2.0}], 'split_exclusions': []}
        b = {'nodeSplit': list(reversed(a['nodeSplit'])), 'split_exclusions': []}
        deep_compare(rc.order_splits(b)[0], rc.order_splits(a)[0])
        c = copy.deepcopy(b); c['nodeSplit'][0]['diff'] = 2.5; self.rejects(deep_compare, rc.order_splits(c)[0], rc.order_splits(a)[0])
        d = copy.deepcopy(a); d['nodeSplit'][1]['comparison'] = 'A vs B'; self.rejects(rc.order_splits, d)

    def test_versions_refused(self):
        rscript = os.environ.get('RSCRIPT') or shutil.which('Rscript')
        if not rscript:
            self.skipTest('Rscript not available')
        script = "source('analysis/versions.R'); x <- REQUIRED; x[['metafor']] <- '0.0.0'; check_versions(x)"
        p = subprocess.run([rscript, '--vanilla', '-e', script], cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(p.returncode, 0); self.assertIn('Wrong R/package versions', p.stderr)
        p = subprocess.run([rscript, '--vanilla', '-e', "source('analysis/versions.R'); check_versions(REQUIRED)"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Safeguards)
    r = unittest.TextTestRunner(verbosity=2).run(suite)
    if not r.wasSuccessful():
        raise SystemExit(1)
    print(f'SAFEGUARDS PASS: {r.testsRun} test groups; planted defects rejected ({len(r.skipped)} skipped)', flush=True)
