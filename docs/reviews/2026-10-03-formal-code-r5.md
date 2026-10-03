# Formal code review R5 and bounded corrections

Reviewed source: `4175cc1af05fbc6a061a8528296757d2b35d3cfa`.
Round: `codex-md-code-20261003-r5`; content digest:
`c4122fdbb38343140f29c3030a84d05ed6f2063d43992da79e37c956fbd6840f`.

The reviewed source passed native CI run `37126680977`: macOS and Ubuntu on
Python 3.11/3.12 each passed 199 tests, and the Python 3.10 rejection guard passed.
All four actual producers started before results were consumed. Opus, Pro and
Flash approved; Astra requested fixes. Official collection was BLOCKED, with all
four entries COMPLETE and none missing. All writers terminated before export and
exact cleanup; source, toolkit and custody bindings remained intact. Export manifest:
`4fd072867fd282a8ddd794f032b83d5c8313b58eb5cd267f46cbef9bc4f34099`.

Actual native final text and the completed handle observation were recorded
unchanged under owner authorization. Unexposed effective model/effort remain null;
these records are observations, not signed runtime attestation. No approval from
this reviewed source transfers to the corrected source.

## Findings and dispositions

Astra reported three findings; Opus approved with nine Minor findings. Flash
retained the prior documented graph-build and Unicode-suffix limitations; Pro had
no findings or open questions. All twelve new claims were adjudicated.

| Claim | Disposition |
| --- | --- |
| Lexical normalization changes symlink/parent traversal | Anchor relative references without collapsing `..` before filesystem lookup. Preserve traversal spelling for aliases and source-bound resolutions while continuing physical-identity deduplication. Ordinary, glob and selected-source paths share the correction; request-scope parent rejection is unchanged. |
| Failed loader prefix produces an exact-looking route total | Mark totals as lower bounds when a common selected loader source could not contribute. Do not propagate an unrelated reference branch's uncertainty into a healthy route. |
| Falsey resolutions bypass list validation | Default only omitted/None Python arguments to an empty list. CLI files must decode to arrays; explicit null and falsey nonarrays reject before output creation. |
| Whitespace-containing labels become nonlocal URLs | Require a complete whitespace-free scheme target. Composite labels stay local/uncertain until a source-bound decision resolves them; valid URI and filename/line controls remain. |
| Config dotfiles are lexed as instructions | Recognize known configuration basenames as evidence leaves. Explicit resolutions can add dependencies; selected guidance takes precedence, and linked extensionless instructions remain supported. This is not generic secret detection. |
| Invalid definition-like prose hides paths | Accept and mask a definition only when the destination and optional complete title consume its whole value. Reuse the existing destination parser and preserve valid next-line definitions. |
| Output creation adds unowned parent directories | Require an existing parent and create only the new output leaf in scan/report/compare. Reflect that requirement in the shipped skill and README. |
| Python 3.11/3.12 path-loop errors escape as exit 1 | Map RuntimeError to operational exit 2 through existing error-receipt paths. Convert source-resolution loops into unverifiable-evidence ValueError. No universal OOM recovery or receipt guarantee is claimed. |
| Whole-file binary cache uses large memory | Confirmed implementation cost, explicitly deferred. The approved contract does not promise bounded memory. Prefix-only binary classification or a new oversized threshold would change semantics; neither is introduced here. |
| Route emission synchronously rewrites each receipt | Confirmed per-row fsync cost, explicitly deferred while preserving the tested atomic interruption receipt. No wall-time dominance was measured. |
| AGENTS test command permits bytecode pollution | Match the documented bytecode-disabled command used by validation and CI. Existing bytecode is not silently removed. |
| Per-directory aggregates omit counts/conditions/frontiers | Preserve existing byte maps and add aggregate/per-scenario summary records. Deduplicate physical text identities, retain scenario-bound conditions and observed frontier counts, and mark known incomplete directories as lower bounds. Cycles and nonlocal URLs do not count as missing coverage. |

The two newly deferred performance costs are distinct from the earlier repeated
graph-construction limitation. README now states all three and makes clear that
`--max-routes` limits emitted routes, not graph work or retained bytes. Unknown
files below inaccessible directories are not counted as absent.

## Verification

Fresh exact `codex-md-improver-executor` instances used canonical source with
`fork_turns="none"`; the leader alone edited source and tests.

- The first private manifest had a leader-authored import error: zero behavior
  methods ran, and that attempt is INVALID, not RED. After correcting the import,
  a fresh executor reproduced 27 assertion failures across 11 methods with zero
  errors; all four controls passed. After implementation, focused GREEN passed 11.
- The initial additional manifest accidentally discovered five imported tests and
  omitted the synthetic Codex-home directory in scan controls. Its concrete
  failures were preserved, but invalid scan passes received no credit. After only
  test setup/import corrections, a fresh executor ran exactly 15 methods with 21
  assertion failures, zero errors and all four control methods passing.
- Final fresh dedicated GREEN passed 26 focused / 225 full tests plus the skill
  validator on native macOS/Python 3.12.13. Canonical source/test fingerprints and
  Git status were unchanged; exact fixtures were empty and removed. No canonical
  bytecode files were created. The scoped read-only source rereview was clean.
- Two fresh Sol/medium/fork-none choices used the revised skill and hypothetical
  output-location scenarios without review history or expected answers. Both
  matched the predeclared control/expectations: proceed with an allowed new leaf
  under an existing parent, or request only an output-location decision when no
  permitted existing parent is established. These are context-limited choices,
  not runtime identity attestation or a replacement for dedicated/formal review.

Local version-0.1.0 candidate ZIP SHA-256:
`569976f1df7f23ff5de5056d62bb00c9ae4886f24cfcffc01590457a21a9ed95`.
It contains 14 selected files plus the embedded manifest. The corrected source
needs its own native CI and a new complete four-leg round. No code admission,
final merge, tag/Release or actual owner installation has occurred.
