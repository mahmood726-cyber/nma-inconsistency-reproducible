# History: plus browser evidence recorded before allmeta v1.8.0

The files in this directory (`pw-gates6.log`, `pw-a11y3.log`, `shots/`) were recorded on 19 Oct 2026 on the panel bytes of
pull request #160 before its review fixes. They are kept unchanged as history. They are **not** the evidence for
allmeta v1.8.0.

The current evidence is `../browser-v180/`: the same 42 tests re-run on the v1.8.0 bytes, 42/42 passed.

One recorded behaviour is superseded. `pw-gates6.log` line 33, "edited valid input re-runs after a pause; invalid input
explains and keeps results", tested the old behaviour: on invalid input the previous results stayed on screen. allmeta
commit 1f5ce9e (the pull request #160 review fix, in v1.8.0) changed `plus-ui.js` so that the page's refusal clears the
results, the plus panel and the export state. The v1.8.0 test is "... invalid input explains and clears results". The same
commit reworded the stability sentence in `shots/walkthrough-result.json`. See `../browser-v180/README.md`.
