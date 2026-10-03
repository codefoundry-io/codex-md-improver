# Formal code review R11 and Git-path corrections

## Correction recorded in R12

R11 correctly repaired filesystem-based Git inventory, but wrongly generalized
that path interpretation to the pinned Codex trust model. Four R11 tests therefore
used incorrect trusted/main expectations. R12 independently checked the actual
pinned source and corrects those expectations to unset/None, while retaining
inventory behavior. The executions below happened as recorded; passing those
incorrect oracles did not establish trust compatibility. See the
[R12 report](2026-10-04-formal-code-r12.md) for the new RED/GREEN and source evidence.


Reviewed source: `ec2696e7a845d778291dacc306eaf865bb5385c0`.
Round: `codex-md-code-20261003-r11`; digest:
`180f0232de87c558042a7039a171c1ac2dc2866a0e004efb9034a984bde0c086`.

[Native CI run 37142961333](https://github.com/codefoundry-io/codex-md-improver/actions/runs/37142961333)
passed all five jobs. macOS Python3.11/3.12 each ran321 methods with320 passes
and one Linux-only skip. Ubuntu each ran321 with314 passes and seven native-alias
skips. All seven alias checks executed on macOS; bytes-name behavior executed on
Ubuntu. The Python3.10 rejection guard passed.

All four producers started before verdict consumption and reached terminal
completion. Astra and Claude requested fixes; Pro returned DO NOT MERGE with a
necessary-coverage question; Flash approved without findings. Official collection
was BLOCKED, all four COMPLETE, no missing entries. Custody/integrity checks passed.
The actual native original and completed handle were retained; hidden runtime
identity remains unexposed. Export manifest:
`f89170a5e3759446be06dc1c60631febe6f3db2f0bd5d2a39b024e0458d635b6`.
The exact managed root was cleaned after export. No vote transfers to new bytes.

## Findings and bounded corrections

| Finding | Disposition |
| --- | --- |
| Astra must-fix: lexical Git-pointer normalization changes `symlink/../` meaning and excludes an ordinary instruction subtree | Accepted. Anchor the pointer without collapsing filesystem-significant parent components. Actual filesystem validation determines storage and worktree ancestry. Relative and absolute pointers, main-checkout pointers, missing intermediate components and benign actual parents are covered. |
| Claude must-fix: a Git indirection can encompass explicit cwd while containing neither the marker parent nor selected project roots | Accepted. Protect explicit cwd in the existing containment check, retaining the selected chain and blocked/partial outcome. Inventory roots and real ordinary `.git` directory behavior remain unchanged. |
| Claude Minor: a `.git` symlink to an ordinary file reenters through an administration frontier and hides that file during directory traversal | Accepted. Reject non-directory `.git` symlinks without following their content as pointer metadata. Existing invalid-marker suppression prevents promotion into graph storage. |
| Pro necessary question: runtime source and tests were not inspected | Retain the valid COMPLETE/DO NOT MERGE result. This is not FAILED_TO_RUN and received no same-basis retry. The next complete round clarifies packet navigation without changing source scope, model, effort, web authorization or permissions. |

The R11 diagnosis confirmed the inventory, cwd and non-directory alias defects,
but incorrectly generalized the pointer interpretation to trust consumers.
The R12 correction above supersedes that consumer-scope claim. The correction adds no comprehensive Git repository validation
or atomic filesystem guarantee. Existing metadata-inferred sibling storage remains
within the established, disclosed boundary.

Pro's actual log records two whole-diff views, a forbidden shell search rejected
by its configured rule, a successful evidence-file view, then the coverage question.
No individual source/test or manifest read was observed. The packet contained the
required files. Logs retain view size summaries, not complete returned pages;
exact clipping, internal reasoning or a capacity cause is unknown. Normal exit
occurred well before the wrapper deadline. The next TASK explains manifest-to-file
mapping, permitted individual native file/page reads and the distinction between
excluded old formal-plan research and included historical code-review evidence.
Genuine necessary unknowns remain reportable. No permission policy was weakened.

## Verification and intermediate regression

Private tests preceded production changes. A fresh exact
codex-md-improver-executor loaded canonical SKILL.md with no inherited turns and
ran17 methods:13 failed methods,26 assertion failures,four passing controls,
zero errors/skips. Setup and custody were valid; all65 canonical and two private
fingerprints, clean Git status and HEAD were preserved. Exact fixture removal
was independently confirmed. Early failures do not prove later assertions ran.

After the initial correction, fresh dedicated GREEN passed17 focused/338 full
methods plus validator, with one Linux-only skip. The executor repeated that
command after verbose output clipping to recover control observations in memory;
both executions preserved all67 fingerprints/status and removed their fixture.
An optional inspection referenced a nonexistent test filename; that inspection
error was separate from valid prerequisites and execution.

Concurrent independent source review found a regression absent from those tests:
using only canonical main-checkout ancestry dropped original alias trust keys.
That intermediate GREEN was not final acceptance. A second fresh exact executor
ran three new cases before the further correction: two alias failures and one
passing canonical-precedence control, zero errors/skips. All67 canonical and one
private fingerprint, status and HEAD stayed unchanged; exact cleanup was confirmed.

At the end of R11, the implementation derived actual main from validated storage, then retained
a normalized original spelling only when its canonical identity matches that main.
An unavailable or mismatching optional lexical candidate cannot replace the
validated root. Main `.git` ownership verification and canonical-before-original
trust precedence remain. A missing lexical-candidate control was added before
final GREEN; it was not part of the three-case pre-fix RED.

Final fresh exact GREEN passed21 focused/342 full methods plus the skill validator
on macOS/Python3.12.13. All seven native-alias checks and all four trust-alias cases
passed. Only the Linux bytes-name fixture was skipped. All68 canonical fingerprints,
Git status and HEAD were unchanged; exact fixture cleanup was independently
confirmed. Part of the verbose display was clipped, while terminal summaries,
custody and native controls were retained. A tool-side interim-exit storage error
was recovered without another execution; actual terminal exit was zero. Executors
wrote only disposable fixtures and stdout. Final independent scoped re-review is
clean; it supplies no formal admission or independent execution claim.

Runtime delta: +13/-2/net11 in discovery.py; total production Python including the
packager is2,463 lines. Three portable test files contain294 lines. README and
review/status documentation are separate; SKILL.md prompt wording is unchanged.

The current local0.1.0 archive contains14 selected files plus its manifest, SHA256:
`5da01134584dd3e922c5678f6bd7ebd3127f5e8b2e5906907842e6779bd2b8d3`.
The corrected commit still requires exact-head native CI and fresh full four-leg
review. Merge, tag/Release and actual owner installation remain separate gates.
