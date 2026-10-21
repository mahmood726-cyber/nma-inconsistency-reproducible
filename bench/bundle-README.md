# P16: NMA inconsistency audit

Start with [RESULTS.md](RESULTS.md). The proposed source changes are in
[fix.patch](fix.patch); the original checkout was not edited.

The page's own JavaScript was run in Node with a minimal DOM adapter. This is
engine, serializer and generated-markup evidence, not a live-browser UI audit.
Multi-arm inputs are explicitly unsupported and are not counted as numerical
parity successes.

Inputs and decisions: corpus.json, dataset-ledger.csv, configuration-ledger.csv,
construction-attempts.json, row-exclusions.json, refusal-ledger.csv and
split-ledger.csv. Evidence: reference.json, reference/, app-original.json,
app-patched.json, focused-*.json and documentation/. Counts and maxima:
results.json and results-*.json.

Reproduction commands and environment-variable overrides are in RESULTS.md.
The supplied source snapshots allow Node reruns without another checkout.
P16-validation.zip contains the portable audit, scripts, source snapshots and
evidence; operational task/runner logs containing machine paths are excluded.
