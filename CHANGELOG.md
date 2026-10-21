# Changelog

## 1.0.0

Initial reproducibility archive for the nma-inconsistency node-splitting and design-by-treatment validation against netmeta 3.7.0. The allmeta release identifiers were filled in the release-fill entry below (v1.8.0, DOI 10.5281/zenodo.23515177).

Plus layer (19 Oct): the leave-one-study-out panel of pull request #160 at commit 5373102 (`plus/`), its R reference check (`plus/validate-plus.R`, sourced by `validate.R`) and its recorded evidence; the v1 layer is unchanged.

## Candidate re-cut, 2026-10-20

Replaced three current primary snapshot files with allmeta v1.8.0 candidate e61378c. Preserved historical patched source, outputs and manifests. Added candidate provenance, exact historical patch reconstruction without Git writes, inventory regeneration, and fresh candidate primary/focused Node captures in the deferred R validation. Release placeholders remained at this step; no fresh R count is claimed.

## Release fill, 2026-10-21

The allmeta release identifiers are filled: v1.8.0 (tag commit 1cb3f84, DOI 10.5281/zenodo.23515177). The snapshots are re-pinned from candidate e61378c to the v1.8.0 bytes: two primary files (export-bar CSS in `hub/shared/results-export.js`; build stamp in `shared/build-info.js`) and four plus files (the pull request #160 fixes in `plus-core.js` and `plus-ui.js`, and the two tests that cover them). All 13 primary and 30 plus files now equal their v1.8.0 Git blobs. On these bytes the Node primary capture and focused capture are byte-identical to the e61378c captures (76601/76601 and 319/319 against the archived netmeta reference), and the plus replay gives PLUS NODE REPLAY 643413/643413. RELEASE_EQUIVALENCE.md records this, including that the plus browser tier was not re-run. The verifier now requires the filled values, the v1.8.0 Git blob ids and the equivalence record; the inventories are re-pinned.

## Browser re-run and new repository, 2026-10-21

The plus browser tier was re-run on the v1.8.0 bytes (Microsoft Edge 155.0.4283.62, Playwright 1.59.1, one worker): 42/42 passed, the same 42 tests as the archived run (`plus/evidence/browser-v180/`, with its runner, site manifest and `expected-browser.json`). v1.8.0 deliberately changed one behaviour, in allmeta 1f5ce9e (the pull request #160 review fix): when the input is invalid, the page's refusal now clears the results, the plus panel and the export state. Before, the explanation was shown and the previous results were kept. The usability test is now "invalid input explains and clears results", and the walkthrough stability sentence is reworded (same numbers). The earlier browser evidence is kept unchanged as history (`plus/evidence/browser/HISTORY.md`). No R reference value changed. The verifier now also checks the v1.8.0 browser log against its expected record, and rejects the superseded "keeps results" test in that run. The repository is published as a new repository with a single commit.
