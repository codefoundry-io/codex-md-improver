# Formal code review R12 and path-contract corrections

Reviewed source: `b1573bf666039ff1ee068eb39fa4a7875b255f32`.
Round: `codex-md-code-20261003-r12`; digest:
`0b641f5b97ba706cc24b58ffa218b7d620c225eba52322361e507cce05476cab`.

[Native CI run 37145295767](https://github.com/codefoundry-io/codex-md-improver/actions/runs/37145295767)
passed all five jobs on the reviewed source. macOS Python 3.11/3.12 each ran 342
methods with 341 passes and one Linux-only skip; Ubuntu each had335 passes and
seven native-alias skips. All seven native alias checks executed on macOS;
bytes-name behavior executed on Ubuntu; the Python 3.10 rejection guard passed.
These results did not cover the defects below.

All four producers started before verdict consumption and reached terminal
completion. Astra and Claude requested fixes; Pro and Flash approved without
findings. Official collection was BLOCKED, all four COMPLETE, no missing entries.
Actual native text and completed handle were retained; hidden runtime identity
remains unexposed. Export and exact managed-root cleanup succeeded. Export manifest:
`88acf888b270129f01787d8edd6793e241daee40f54d43c7670d3f886a016153`.
All four legs had web research permission. No verdict transfers to changed bytes.

## Confirmed findings

- Native case aliases could bypass output containment in scan, report, compare,
  linked-directory checks, owned-output inventory exclusion and package creation.
  A pure shared helper establishes native existing-path identity. CLI outputs
  retain their required existing parent; package outputs may have missing outside
  parents, and saved report roots may no longer exist. Native stat preserves
  non-missing errors before permissive missing-path normalization. Graph checks
  reuse the already canonical visited target; original report/reference spellings
  remain intact. Package code loads only the helper from its fixed repository
  source, never Python from a selected candidate source tree.
- R11 wrongly extended filesystem-aware inventory semantics to the pinned Codex
  trust model. Trust paths are lexically normalized before validation; a validated
  lexical main key is required and cannot be replaced by a different canonical
  main. The implementation separates these consumers and applies lexical joining
  to the linked pointer, backlink, commondir and main pointer. Inventory retains
  actual filesystem behavior. Canonical-before-original key precedence remains.
- NUL-bearing Git metadata could be truncated by Darwin libc path conversion,
  granting false trust; on Linux an invalid path could escape as an input error.
  The metadata parser now rejects NUL before path handling. The pure native helper
  also rejects embedded NUL instead of passing it to a C string API.

## Correction to the R11 oracle

The four earlier expected trusted/main results for relative and absolute
symlink-parent worktrees, a significant-parent main pointer, and missing lexical
main were wrong. R11 execution happened as recorded, but those expectations
incorrectly asserted compatibility. They are now unset/None. The historical R11
report carries a correction notice; its original observations are not erased.

The approved plan has compatible contracts: actual Git storage inventory and a
specific Codex trust implementation. Independent read-only diagnosis fetched the
actual pinned commit after native web cache misses:

- [Trust resolution and main ownership](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/git-utils/src/trust.rs#L139-L232).
- [UTF-8 native path joining](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/utils/path-uri/src/native_path_bytes.rs#L11-L14).
- [PathUri lexical normalization and NUL rejection](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/utils/path-uri/src/lib.rs#L432-L534).
- [Absolute path normalization](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/utils/path-uri/src/absolute_path_normalization.rs#L18-L27).

Fetched code was inspected as text, not executed. This correction follows the
existing approved contract, without new product semantics or repeated broad
research.

## Verification

Two fresh exact codex-md-improver-executor instances loaded canonical SKILL.md
with no inherited turns before production changes.

The output RED ran 17 methods: nine failing methods, 19 assertion failures,seven
passes, one case-sensitive-volume skip,zero errors. Native aliases existed and
passed samefile checks. All 68 canonical fingerprints, two private scenario
fingerprints, packager hash, HEAD and clean status were preserved. The exact
fixture was removed and independently absent. Early assertions stopped some
later checks: packaging RED proves output creation and copied-resource byte
preservation, without claiming its later parent-absence/rejection assertions ran.

The trust RED ran 12 methods: nine failures, three passing controls,zero errors or
skips. It reproduced the four incorrect trusted results, false unset after a
lexically canceled missing component, and four NUL false-trust results. Normal
relative worktree, original main alias and canonical-key precedence controls
passed. All 68 canonical fingerprints, private scenario, harness, HEAD and status
were preserved; exact fixture removal was independently confirmed. NUL failures
stopped before readable-chain and project-setting assertions, so those downstream
outcomes were not observed in RED.

Root then corrected production and copied portable regressions, inspecting each
PROJECT binding. Three additional controls for raw ENOTDIR preservation and
lexical backlink/commondir missing components were added after RED; they are not
claimed as pre-fix evidence.

The first fresh GREEN passed 32 focused methods (one case-sensitive skip), but
the full374-method run failed the existing synthetic runpy version-guard probe;
the validator passed. A new top-level helper import preceded the guard. All 72
fingerprints, status, HEAD and separate packager hash remained unchanged, and
the fixture was removed. That intermediate run is not complete GREEN.

Independent Sol source review also found a remaining pinned-path mismatch:
Python preserves exactly two leading POSIX slashes, while PathUri normalizes them
to one. A third fresh exact executor ran a new negative/control pair before the
correction: one false-trust failure and one valid single-root key/settings pass,
zero errors or skips. Later negative settings assertions did not execute.
All 72 fingerprints, private scenario, status, HEAD and packager were preserved;
the exact fixture was removed and independently absent.

Root then normalized the leading POSIX root in the lexical trust helper and
moved command helper imports behind the Python version guard. Inventory pointers
remain unchanged. Independent scoped rereview of these final corrections is
clean, without claiming independent execution.

Final fresh exact GREEN passed 34 focused methods (33 passes, one native
case-sensitive control skip),376 full methods (374 passes, two skips), and the
skill validator on macOS/Python 3.12.13. Version-guard, NUL downstream settings,
double-slash negative/settings control, native containment and distribution
checks passed. The terminal display clipped part of the full suite: the second
skip identity was not recovered or asserted, and no rerun occurred.

All 73 canonical source/test fingerprints, HEAD and Git status stayed unchanged;
the packager and harness hashes were independently preserved. Session62211
reached terminal exit0; exact fixture removal and independent absence were
confirmed. Executors wrote only the named fixtures and stdout. Distribution
tests exercise15 resources, reproducibility and copied-subtree execution; they
do not prove actual owner installation or fresh official discovery.

Production delta is +83/-45/net38 across four existing modules and one new pure
helper, totaling 2,501 production Python lines including the packager. Four new
test files contain 471 lines; four previous test expectations changed separately.
The resource allowlist grows from 14 to 15 to ship the shared helper. Tests and
documentation are separate from the production count; SKILL.md wording is unchanged.

The local 0.1.0 candidate contains 15 selected files plus its manifest, SHA256:

`3552b1f9b513b33e2ac902b3c69ae2748d5c9ba0df128df0c6fb7231df84dc99`.

This candidate was built after final GREEN; it is not a release or installation.

The corrected commit requires exact-head native CI and fresh complete four-leg
review. Merge, tag/Release and actual owner installation remain separate gates.
