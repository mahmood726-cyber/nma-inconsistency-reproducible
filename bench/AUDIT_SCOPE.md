# Scope and acceptance criteria

Validate the nma-inconsistency page and relevant shared code from the recorded
allmeta source commit against installed R 4.6.0, netmeta 3.7.0 and meta 8.5.0.
Enumerate offline netmeta/metadat datasets, record every candidate and exclusion,
and exercise every offered model (FE, DL, PM). Validate signed node splits,
their SEs, differences, z and p; design-by-treatment Q/df/p; network estimates,
heterogeneity, membership, displayed/exported values, refusals and caps.

Execute shipped app code. Headless Edge is preferred; Node is permitted for the
pure JavaScript engine. Document the execution route and its limitations.
Closed-form comparisons use 1e-9 relative to max(1,abs(reference)); iterative
quantities use 1e-6 with convergence settings stated; p-values use 1e-9 absolute.
Keys, coverage, membership and displayed strings at their shown precision are
exact. Missing/nonfinite evidence never passes.

Keep the source checkout unchanged. Produce an app-only unified fix.patch for
defects, rerun, and preserve before/after counts, fault examples, source locations,
reference documentation and honest limits. Do not commit or push. Keep
PROGRESS.md current. Portable deliverables contain no machine-specific paths.
