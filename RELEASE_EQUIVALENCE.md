# Equivalence of the archived snapshots with allmeta v1.8.0

allmeta v1.8.0: tag `v1.8.0`, commit `1cb3f8409c7af75ed41f7e1811f9c502f900fc79`, DOI 10.5281/zenodo.23515177.
The archive was re-cut against candidate `e61378ce260911af311fc45a3f91e239f15f7c5b` (branch `cand/v180-c-1119`).
That commit is not an ancestor of v1.8.0, which re-merged the same pull requests. The snapshots are therefore
compared and re-pinned by bytes.

Of the 43 snapshot files (13 in `app/patched/`, 30 in `plus/app/` excluding `SOURCE.json`), 37 were already
byte-identical to their v1.8.0 blobs. The other six differed and were replaced with the v1.8.0 bytes:

| File | Difference from e61378c to v1.8.0 | Class |
|---|---|---|
| `app/patched/hub/shared/results-export.js` | export-bar CSS adds `flex-wrap:wrap;max-width:100%` | non-engine (layout only) |
| `app/patched/shared/build-info.js` | build stamp (version, sha, build time) | non-engine (display only) |
| `plus/app/nma-inconsistency/plus-core.js` | `globalFlip` is now false unless both global p-values are finite; the stability sentence reads "Among removals with a testable global p-value, ..." | engine |
| `plus/app/nma-inconsistency/plus-ui.js` | a debounced edit now runs the page on invalid input too, so a refusal clears the base result and the panel state (before: explain and keep the previous results) | engine (user interface behaviour) |
| `plus/app/hub/shared/tests/nma-inconsistency-plus.node.cjs` | assertion `failed.length === 0` instead of `deepEqual(failed.slice(0,5), [])` | test |
| `plus/app/hub/shared/tests/nma-inconsistency-usability.spec.mjs` | browser spec now expects invalid input to clear results | test |

After the re-pin, all 43 files are byte-identical to the v1.8.0 Git blobs. `app/original/` and
`app/historical-patched/` are historical snapshots and unchanged.

Check by execution (21 Oct 2026, Node v24.13.0, Python 3.13.13, Windows), on the v1.8.0 bytes:

- Plus replay: `node plus/app/nma-inconsistency/validate/derive-plus-checks.cjs` (the step that `plus/validate-plus.R`
  runs; it loads `plus-core.js`) printed `PLUS NODE REPLAY 643413/643413` (loo 619,763; estimators 20,072; text 935;
  graph 2,643; boundary 0). This is the archived count in `plus/evidence/node-replay/derive1.log`. The full log is
  byte-identical to the same run on the e61378c bytes. `--tamper` still fails: 643412/643413.
- Primary and focused captures: the unchanged `bench/run_app.cjs patched` and `bench/test_focused.cjs patched`, staged as
  `analysis/capture_candidate.py` does but with the archived focused oracles `results/normal-reference.json` and
  `results/bus-reference.json`. The outputs are byte-identical to the same run on the e61378c bytes:
  - `app-patched.json`: SHA-256 `461915dec647bacece03d16aefdb02f648f454c81b6b6319407c4a0199b6a24c` (540 configurations);
  - `focused-patched.json`: SHA-256 `30dc8eebca4cddf0610748c9cea5beb01fe720c87595fbe8a897c5be48e31489`, 319/319 focused
    checks pass.
- `analysis/compare_archive.py patched` on that capture against the archived netmeta reference `results/reference/`:
  76601/76601 checks pass. The per-quantity counts equal `expected/paper_values.json` (`check_expected`).
- `analysis/verify_archive.py`: 13/13 snapshot files and 30/30 plus files match the v1.8.0 pins and blob ids.
- Plus browser tier (21 Oct 2026; Microsoft Edge 155.0.4283.62, Playwright 1.59.1, one worker), re-run on a site whose 49
  files all equal their 1cb3f84 blobs (`plus/evidence/browser-v180/`): **42/42 passed**, the same 42 tests as the archived
  `plus/evidence/browser/pw-gates6.log` (42/42). In-page plus replay 643413/643413; tampered reference 643412/643413 with
  the same first failure; pinned base replay, tamper and pin-refusal tests, and live R FE/DL/PM pass; walkthrough clicks
  identical (total 3); axe 0 violations (29 passes); `fig2-capture.json` byte-identical. Two results differ, as v1.8.0
  intends:
  - usability test 23 is now "invalid input explains and clears results" (before: "... and keeps results");
  - the walkthrough stability sentence now begins "Among removals with a testable global p-value" (same numbers).

## The plus-ui.js behaviour change

allmeta commit `1f5ce9e400762334c702b9e665ab0dcd0233c641`, the pull request #160 review fix (merged into v1.8.0 by
`d97ac74`), changed the debounced input handler in `plus-ui.js`:

```diff
-        // Auto-run only input the page would accept; otherwise explain and keep results.
-        if (!window.inputIssue(window.parse(src.value)) && src.value !== shownText) window.run();
+        // Run refusals too, so the base result and observed plus/export state clear.
+        if (src.value !== shownText) window.run();
```

Before, invalid input was explained but the previous results stayed on screen, so the results, plus panel and exports no
longer matched the input box. The review reported this as a P1 finding (stale results). In v1.8.0 the page's own
refusal runs and clears them. The input message still explains the problem. The same commit changed the usability spec to
assert this, and changed `globalFlip` and the stability sentence in `plus-core.js`. The archived numerical results are not
affected (the plus replay is 643413/643413 before and after). The earlier browser evidence stays in
`plus/evidence/browser/` as labelled history (`HISTORY.md`). The current expected values are in
`plus/evidence/browser-v180/expected-browser.json`.

Not re-run:

- R. The fresh netmeta refit and the plus R refit in `validate.R` (several hours) were not re-run; the R references do
  not depend on the app. No R reference value was changed.
- The portfolio a11y sweep `plus/evidence/browser/pw-a11y3.log` (76 apps). It needs the whole allmeta portfolio.

The numerical results of the archive (primary, focused and the plus leave-one-study-out replay) and the plus browser tier
therefore apply to allmeta v1.8.0, with the intended v1.8.0 behaviour that invalid input clears results.
