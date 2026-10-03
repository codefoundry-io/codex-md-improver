# Formal code review R8 and bounded corrections

Reviewed source: `9de4be8fb4c5fde614da6ddbd0270b5e8f01fc02`.
Round: `codex-md-code-20261003-r8`; digest:
`3aaf9d281db588bba7acd6e67ba06932d62f476896cd7124daef082c6457d7a5`.

[Native CI run 37134812267](https://github.com/codefoundry-io/codex-md-improver/actions/runs/37134812267)
passed on that exact source. Ubuntu Python 3.11/3.12 each passed 262 tests;
macOS each passed 261 with one Linux-only skip. The Python 3.10 rejection guard
passed. The portable test-location binding check passed in all four matrix jobs.

All four producers started before verdict consumption and completed. Astra and
Opus requested fixes; Pro and Flash approved without findings. Official collection
was BLOCKED, all entries COMPLETE, none missing. The collector's custody and
integrity checks passed. Evidence was exported and the exact managed root cleaned.
Export manifest: `a807103c1039fb670a096a26a1652e0f5cd69ebecd97e1c4144f8125196eb66c`.
The native original reply and observed completed handle were retained under owner
authorization. Hidden runtime model/effort remain unexposed. No approval transfers
to changed source.

## Findings and corrections

| Finding | Disposition |
| --- | --- |
| Astra must-fix and Opus Minor: duplicate Markdown definitions select the last destination | Accepted. Preserve the first accepted matching definition while retaining all definition spans. This follows [CommonMark 0.31.2, example 204](https://spec.commonmark.org/0.31.2/#example-204), checked 2026-10-04. Tests cover full, collapsed and shortcut references, casefolded labels, a nested required dependency, readable decoys and a missing first target. Existing parser and occupied-span conventions remain. |
| Astra must-fix: atomic replacement between graph and candidate phases creates candidates with the wrong source hash | Accepted. Compare returned raw bytes with the graph node hash before decoding/extraction. A mismatch follows the existing changed-source frontier and directory-summary refresh. Identical bytes on a new inode remain valid. Original graph hashes and byte snapshots are retained. |
| Opus must-fix: native case aliases bypass SKILL.md and Git exclusions | Accepted. Reuse the existing native canonical-spelling helper for graph and assessment boundary checks. Preserve requested aliases for source bindings and reference bases. Graph canonicalization errors remain branch-local failures. Native tests verify actual case-alias identity, no excluded-byte reads, no expansion/candidates and assessment refusal. An actually lowercase skill.md remains an ordinary file. |
| Opus Minor: README promises a complete route stream even when capped | Accepted. Describe completeness as conditional on --max-routes and point to the existing truncation indicators. |

The scoped source review then identified a separate existing omission in report
revalidation. An authentic scan can record external Git administration storage
and an ordinary readable guide. Retargeting the guide after the scan to a
same-byte symlink inside that recorded storage passed the hash and filename
checks. This requires neither a forged audit nor concurrent filesystem racing.
Reporting now checks its recorded Git administration roots before evidence reads.
The correction uses the scanner's existing canonical roots; it does not discover
new storage or claim atomic protection. All evidence, reviewed-source and
affected-reference consumers share the check. Normal sources and similarly named
sibling directories remain accepted.

## Verification and process limits

Fresh instances of the exact codex-md-improver-executor loaded the canonical
source with no inherited turns. Executors wrote only their exact disposable
fixtures and returned stdout; the leader authored source/tests and retained
evidence. No installed or copied skill substituted for canonical behavior tests.

The first eight-method RED run had intended failures but also incorrect test
expectations: invalid definition prose could itself create a reference, and
preserved path aliases were compared against normalized paths. That qualified
result and its inputs were retained. The leader corrected the controls before
any production change. Fresh RED then ran 13 methods: 10 assertion failures in
eight methods, five passing controls, zero errors/skips. All four native case
fixtures executed on the local case-insensitive macOS volume. Assertions after
an initial failure are not counted as independently observed RED evidence.

After the first corrections, fresh GREEN passed 13 focused and 275 full methods
plus the validator. The later storage regression used an authentic scan and
verified frontier/hash bindings before retargeting. Its initial executor stopped
before executing any tests when the leader noticed incomplete semantic coverage
in a control input. The unrun draft was retained and corrected. A new executor
observed the intended rejection failure and two passing controls, with no errors.
Only then did the leader add the recorded-storage check.

Final fresh GREEN passed 16 focused methods with no skips and 278 full methods
with one Linux-only filename skip, plus the skill validator, on macOS/Python
3.12.13. All four native case-alias checks executed and passed. All 57 canonical
source/test fingerprints, Git status and base HEAD remained unchanged; fixtures
were empty and independently confirmed removed. The tool renderer truncated some
verbose full-suite names, but retained the terminal summary, validator result and
complete final fingerprint receipt. Independent scoped re-review was clean.

Production delta: +14/-7/net7 lines across three runtime files; total production
Python including the packager is 2,385 lines. Four new test files contain 317
lines, with portable bindings checked in the actual copied test sources. README
and review/status documentation are separate. No SKILL.md prompt wording changed.

The final local version 0.1.0 candidate contains 14 selected files plus an embedded
manifest. Archive SHA-256:
`70c4fded9329fdbc2f4c9fac1f4de08cf87ee1e712d6990be69da578905736fa`.
The earlier R8 candidate is retained as evidence for the first GREEN only.

The corrected commit still requires native CI and a full fresh four-leg review.
Case-alias fixtures explicitly skip where the native alias does not exist; a
case-sensitive host does not supply macOS alias proof. Existing performance,
heuristic parsing and non-atomic filesystem limits remain. Final merge, tag/Release
and actual owner installation retain separate approval boundaries.
