# Pre-merge code review R1 and corrections

The first complete public-v2 code round reviewed commit `31771f8` with content
digest `b630de74e766ac82ad78adee235f63a0bb2c80dc8f76ce90e0315fedbd37dc12`.
All four legs completed on that basis. Opus reported ten findings and Astra five,
both requesting fixes; Google Pro and Flash approved without findings. Official
collection returned `BLOCKED` with no missing entries. No approval transfers to
the amended source. The exact round was exported and its managed temporary root
cleaned after all writers terminated.

## Verified corrections

- Mixed read/output/example verbs no longer silently discard a possible read
  dependency. They remain uncertain until a source-bound decision resolves them.
- Defined shortcut Markdown references are extracted. Anchor-only and URL
  occurrences no longer become invented missing local files.
- Loader-selected guidance and extensionless linked instructions extract outgoing
  references independently of suffix; `.markdown` uses Markdown candidate rules.
- Finite glob expansion preserves denied enumeration frontiers alongside readable
  matches. Candidate-pass read failures likewise preserve partial status, usable
  siblings and route output rather than aborting the whole scan.
- Persisted reviewed-source claims must be unique readable aliases in the same
  snapshot. A path string cannot resolve a finding about an uncovered source;
  comparison still does not reread historical source files.
- Directory subtotals retain scenario identity. Shared path totals count the
  physical union instead of whichever scenario was visited last.
- Unknown trust retains uncertainty where eligible project layers could change
  settings. Confirmed absence still permits the declared defaults hypothesis,
  and final explicit session overrides remain effective.
- Independent scenario IDs include inventory root and cwd, retaining overlapping
  project selections without collisions. Supplied client/version and compact
  winning-value provenance remain distinct from live runtime attestation.
- Current provenance now records the approved public-history decision. The lexer
  omits obvious unquoted numeric-version/abbreviation leads and fixes the `e.g.`
  boundary; ambiguous path/command candidates remain available for semantic review.

The leader rejected blanket suppression of ambiguous names, automatic traversal of
unused reference definitions, prohibition of overlapping project roots, a generic
command parser and full configuration histories. These are not needed to correct
the evidenced failures within the approved contracts.

## Verification and limits

A first fresh exact `codex-md-improver-executor` reproduced nine bounded private
methods with 15 assertion failures and zero errors. The canonical regression set
then reproduced all 15 methods with 21 assertion failures and zero errors before
production edits. A test-path portability cleanup initially omitted an import;
the leader's focused run caught that test error, which was repaired explicitly.
It was not counted as behavioral RED.

Fresh dedicated GREEN passed 15 focused and 165 full tests plus the skill
validator. A separate read-only Sol review then found a numeric-URI regression
in the correction: URL ports and opaque numeric payloads were mistaken for line
suffixes. A new exact-executor RED observed three assertion failures in one method
while the `guide.md:12` control passed. After the bounded fix, final fresh dedicated
GREEN passed 16 focused and 166 full tests plus the validator. The scoped rereview
found no remaining concrete defect in that branch.

Every accepted executor preserved source/test fingerprints and Git status and
removed its exact disposable fixture. Effective runtime identity remains
unexposed. Local host observation: native macOS, Python 3.12.13. Distribution unit
checks passed within the suite; a new 14-file candidate archive was generated with
SHA-256 `eaee2eff3c0b2aa17c7672499533cbd0ced4e40b690606dbc38d1b2595bf6e02`.
This is neither a tagged release nor fresh installed discovery.

Native CI for the amended commit and a new full four-leg pre-merge round follow
these local corrections. Final merge, release and actual installation remain
separate owner gates. Private raw review and execution custody is not published.
