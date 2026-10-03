# Formal code review R13 and bounded corrections

Reviewed source: `6d3f876b11ee2377905d6a6662ca38fdc075edce`.
Round: `codex-md-code-20261003-r13`; digest:
`234574c1370f02cb6f86285f3e842e31b742da473bb26a86c4418da3d5f2b000`.

[Exact-source CI run 37148928816](https://github.com/codefoundry-io/codex-md-improver/actions/runs/37148928816)
passed all five jobs. Each macOS Python 3.11/3.12 job ran376 methods with374
passes and two skips; each Ubuntu job had357 passes and19 native-alias skips.
All19 alias checks passed on macOS; bytes-name and distinct-case checks passed
on Ubuntu; the Python3.10 guard passed. This evidence did not cover the R13 defects.

All four producers started before verdict consumption and completed. Astra
requested two fixes; Claude approved with three Minor findings and one optional
hardening item; Pro and Flash approved without findings. Official collection
was BLOCKED with all four COMPLETE and no missing entry. The actual native
original and completed handle were retained; hidden runtime identity remains
unexposed. All four legs had web permission. Export and exact cleanup succeeded;
export manifest:
`830797b6f6e4a7843338ca79acf9aeab65177b431ccb898ba4cf576ff1a1946c`.

## Finding dispositions

- Explicit environment groups bypassed the existing Git-administration cwd
  exclusion. The correction classifies each member before instruction selection
  or content reads, using lexical .git boundaries and canonical identified storage.
  Excluded members retain ordered identity and supplied settings as empty
  unresolved records, with no project/global reference roots or invented loader
  failure. Unknown contribution propagates through the shared budget; known
  gating and exhaustion retain zero inclusion. Group-level global candidate
  accounting remains available.
- Trust metadata incorrectly stripped VT along with Rust ASCII whitespace.
  Trust parsing now trims SPACE/TAB/LF/FF/CR while preserving literal VT paths;
  inventory parsing keeps its existing behavior. This applies to linked/main
  pointers, backlink and commondir, preserving NUL and regular-file checks.
- Unused malformed declared reference bases bypassed validation. All aliases
  and exact base shapes are now validated before output creation, using the same
  pure validator as occurrence resolution. Valid unmatched absolute aliases,
  nonexistent paths and lexical parent components remain accepted; no alias
  existence or matching requirement was added.
- The README now qualifies native case-alias evidence: tested on macOS; native
  Linux casefold volumes remain untested by ordinary case-sensitive Ubuntu CI.
- Non-B packager bytecode behavior remains optional hardening outside the
  documented `python3 -B` invocation. No packaging behavior was changed.

The other Astra finding proposed normalizing direct cwd original trust keys.
That correction is rejected: approved plan line71 requires canonical lookup
followed by the original supplied spelling. The pinned
[project trust lookup](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/config/src/project_trust.rs#L41-L69)
preserves that original key, including its POSIX spelling. Git metadata
[PathUri joins](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/git-utils/src/trust.rs#L139-L232)
are a different consumer boundary. Applying their normalization to direct keys
would contradict the approved contract. Direct-key and inventory aliases remain
unchanged. The R12 description of single-root normalization refers specifically
to those Git metadata joins, not every supplied key.

The trust-trim correction follows the pinned metadata consumer's trim_ascii calls
and Rust's [ASCII whitespace definition](https://doc.rust-lang.org/std/primitive.u8.html#method.is_ascii_whitespace).
These are bounded checks against the existing design, not new scope or a repeat
of the earlier broad research.

## Verification

Before production edits, a fresh exact codex-md-improver-executor with no inherited
turns loaded canonical SKILL.md and ran26 methods once:21 failed methods,
45 assertion failure records, five passing controls, zero errors or skips.
Group exclusions had nine failing methods/ten records; trust trimming had seven;
invalid bases had five failing methods/28 records. Five controls passed, including
normal shared budgets, unchanged inventory trimming, ordinary ASCII padding,
all four valid base shapes and relative document-base resolution.

Group failures prove excluded physical content reads; the CLI failure also
showed an excluded source with one included byte. Later graph/budget assertions
were not reached. Trust failures show five false-trusted and two literal-VT
false-unset results; commondir settings assertions were not reached. All28 invalid
base subcases returned0 instead2; later output-absence assertions were not reached.
All73 canonical source/test fingerprints, three private tests, HEAD/status and
separate harness/packager hashes were preserved. Actual session18721 terminated
with exit1. Exact fixture removal and independent absence were confirmed.

Root then applied the bounded correction and copied portable tests. Production
delta is +35/-19/net16 across two runtime files; three new test files contain427
lines and26 methods. README and review/status documentation are counted separately.
SKILL.md wording, packaging resources and direct cwd trust semantics are unchanged.

Fresh exact GREEN then passed26 focused methods,402 full methods (400 passes,
two native-platform skips) and the skill validator on macOS/Python3.12.13.
There were zero failures, errors or failed subtests. Distribution tests passed,
including the15-resource allowlist, reproducibility, manifest/hash validation and
isolated copied-subtree execution. This is disposable distribution evidence,
not actual installation.

The two skips were the Linux bytes-name fixture and a distinct case-sensitive
sibling control unavailable on this case-insensitive volume. All new downstream
assertions executed: no excluded instruction reads or graph seeds, unknown and
known-zero shared-budget behavior, literal-VT trust, unchanged project settings
after invalid commondir, and malformed-input refusal before output creation.
Valid base and inventory controls passed.

All76 canonical source/test fingerprints, HEAD/status and separate harness/
packager hashes matched before and after. Actual session72401 reached terminal
exit0; results were [0,0,0]. The complete original returned output was retained;
a clipped display segment was recovered from that output without rerunning.
The exact fixture was empty, removed and independently absent. A separate fresh
Sol/high source review found no remaining concrete scoped defect and preserved
all inspected fingerprints/status. It executed no candidate code or tests.


The local 0.1.0 candidate contains15 selected resources plus its manifest, SHA256:

`3ee64907b6202d4f3df15a21699b19690d698f108c5283eab7e5186ade09535c`.

This candidate was built after GREEN and is not a release or installation.

The corrected commit requires exact-head native CI and a fresh complete four-leg
review. No earlier verdict transfers. Merge, tag/Release and actual owner
installation remain separate approval boundaries.
