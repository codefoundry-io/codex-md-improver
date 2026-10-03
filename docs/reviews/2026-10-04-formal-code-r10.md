# Formal code review R10 and bounded corrections

Reviewed source: `a62304caf6c9165660aa210ede7e55ab39cb83f5`.
Round: `codex-md-code-20261003-r10`; digest:
`1c179dc8a4ed66cbd2c5e04f297cddcc17b6471e524edc008c7cdab6c007ddfb`.

[Native CI run 37139934194](https://github.com/codefoundry-io/codex-md-improver/actions/runs/37139934194)
passed all five jobs on that source. macOS Python 3.11/3.12 each ran 297 methods,
with 296 passes and one Linux-only skip. Ubuntu each ran 297, with 292 passes and
five native-alias skips. All five alias tests executed on macOS; the bytes-name
fixture executed on Ubuntu. The Python 3.10 rejection guard passed.

All four producers started before verdict consumption and completed. Astra
approved with one Minor finding; Claude requested fixes with one must-fix and
three Minor findings. Pro and Flash approved without findings. Official
collection was BLOCKED, all entries COMPLETE, none missing. Custody and integrity
checks passed. The native original and actual completed handle were recorded;
hidden runtime identity remains unexposed. Export manifest:
`cb827aaf9149bddc0b9094c86dabe15659b32ade81015147a851a355aa2d9e2f`.
The exact managed root was cleaned after export. No vote transfers to new bytes.

## Findings and corrections

| Finding | Disposition |
| --- | --- |
| Claude must-fix: a Git pointer to self, an ancestor or another selected project erases required inventory and can report complete | Accepted. Reject indirections whose canonical target contains the marker parent or a selected project root. Retain a blocked `invalid_git_pointer` frontier and project chains. Loader marker detection and trust fallback remain separate. |
| Claude Minor: candidate canonicalization RuntimeError escapes the branch handler on supported Linux/Python | Accepted. Map RuntimeError through the existing branch-local frontier, preserving healthy siblings and clearing stale expansion. Test the injected exception separately from a completed native symlink loop. |
| Claude Minor: a stored SKILL.md symlink is excluded through a directory route but read through a direct file route | Accepted under the existing owner contract that SKILL links terminate at an excluded boundary. Pass the original path and canonical target to the shared classifier. Inspect relevant parent metadata for an exact stored SKILL.md entry and matching file identity, without listing unrelated parents. This auditor contract does not depend on upstream skill-installation behavior. |
| Astra Minor: a directory named SKILL.md is mistaken for a skill file | Accepted. Apply SKILL entrypoint exclusion only to regular-file targets. Reuse graph metadata and keep directory-content checks. A named directory traverses normally; a named FIFO remains a special-file frontier. |
| Claude Minor: a whitespace-only invalid definition masks the plain path on its line | Accepted. Only valid, nonempty definitions occupy spans. Invalid Markdown labels create no Markdown dependency, but their plain paths remain uncertain evidence or explicit read dependencies according to their own prose context. |

Independent source diagnosis found the same Git inventory erasure through a
directory symlink marker, such as `.git -> .`. That related case received another
fresh RED before implementation. Invalid marker aliases must also be omitted
from administration frontiers; otherwise graph context resolves the alias back
to the rejected project root. Blocked evidence remains. Real ordinary `.git`
directories and valid external or in-tree sibling storage retain their behavior.

The Git correction uses path metadata only. It does not introduce comprehensive
Git structure authentication or read additional HEAD/backlink contents. Existing
nonancestor sibling-pointer targets remain inferred storage under the established
contract; README now states that limitation. Native Linux casefold-volume behavior
remains statically reasoned, not tested by ordinary case-sensitive Ubuntu CI.

The earlier R9 test that expected no occurrences for an invalid whitespace label
was incorrect. It suppressed the plain-path evidence required by the existing R5
contract. Its original execution remains historical evidence; the expectation
has been corrected and the process error is retained here rather than hidden.

## Verification

The root authored private scenarios before production changes. A fresh exact
codex-md-improver-executor loaded the canonical skill with no inherited turns and
ran 20 methods: 12 failed methods, 26 assertion failures, eight passes, zero errors
or skips. All controls passed. Both native case-retarget tests executed. The
Linux-style RuntimeError was explicitly injected; the native completed loop was
a separate passing macOS control. Early failed assertions do not establish later
unexecuted assertions within the same subcase.

After the directory-symlink diagnosis, the original Git test source was retained
and the private suite expanded before any production edit. Another fresh exact
executor ran ten Git methods: seven failed methods, 25 assertion failures, three
passing storage controls, zero errors/skips. This reproduced both inventory loss
and administration-frontier leakage into graph context. Both RED runs preserved
all 60 canonical source/test fingerprints, five private test fingerprints, clean
Git status and HEAD. Exact fixtures were empty, removed and independently absent.
Repeated middle tracebacks in the first RED were partly tool-clipped; actual
method results, terminal summary and custody evidence remained visible.

Only then did the root apply the corrections and copy five tests with verified
portable PROJECT bindings. Fresh exact GREEN passed 24 focused methods with no
skips, 321 full methods with one Linux-only bytes-name skip, and the skill validator
on macOS/Python 3.12.13. All seven native-alias checks ran. Actual native loop and
injected RuntimeError checks both passed. All 65 canonical source/test fingerprints,
Git status and HEAD remained unchanged; exact cleanup was independently confirmed.
Executors wrote only their disposable fixtures and returned stdout.

Independent scoped Sol review found no remaining concrete defect and preserved
source/status. It supplied no formal admission or independent execution claim.
Runtime delta is +33/-15/net18 lines across four modules; total production Python
including the packager is 2,452 lines. Five new tests contain 385 lines; the R9
expectation correction is +8/-2. README and review/status documentation are separate.
SKILL.md prompt wording is unchanged.

The local version 0.1.0 candidate contains 14 selected files plus its embedded
manifest. Archive SHA-256:
`60e994e45b745d5a20b584d405fe1191d27ab81adf4e1c19a7914e6cf951dda0`.
The corrected commit still needs native CI and a complete fresh four-leg review.
Heuristic parsing, full-route costs and non-atomic filesystem limits remain.
Merge, tag/Release and actual owner installation retain separate approval gates.
