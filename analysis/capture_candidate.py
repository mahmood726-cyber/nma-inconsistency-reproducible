"""Run the unchanged historical Node capture commands on the candidate.

Called by validate.R after fresh focused R oracles exist. Results remain in
.validate-work/capture; archived results and expected counts are never replaced.
"""
import shutil
import subprocess
import sys
from pathlib import Path
from common import ROOT, dump, read, sha
from verify_archive import candidate_sources


def capture(work):
    candidate_sources()
    capture_dir = work / 'capture'
    capture_dir.mkdir()  # Refuse stale captures.
    shutil.copytree(ROOT / 'app/patched', capture_dir / 'app-patched')
    for name in ['run_app.cjs', 'test_focused.cjs']:
        shutil.copyfile(ROOT / 'bench' / name, capture_dir / name)
    shutil.copyfile(ROOT / 'data/corpus.json', capture_dir / 'corpus.json')
    for name in ['normal-reference.json', 'bus-reference.json']:
        shutil.copyfile(work / name, capture_dir / name)
    for script in ['run_app.cjs', 'test_focused.cjs']:
        subprocess.run(['node', script, 'patched'], cwd=capture_dir, check=True)
    pins = read(ROOT / 'app/candidate-source.json')
    dump(capture_dir / 'SOURCE.json', dict(commit=pins['commit'], files=pins['files'],
         outputs={name: sha(capture_dir / name) for name in ['app-patched.json', 'focused-patched.json']}))
    print('CANDIDATE CAPTURE PASS: fresh primary and focused Node observations', flush=True)


if __name__ == '__main__':
    capture(Path(sys.argv[1]).resolve())
