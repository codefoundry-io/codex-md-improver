# Formal code review R9 and bounded corrections

Reviewed source: `ec2a0de07f0fc981937858ff7fe458352c10a7ab`.
Round: `codex-md-code-20261003-r9`; digest:
`33f735965e8987fa301b0cd6f0bb56b0d017c16fb757e8c08819e515b6624296`.

[Native CI run 37137834714](https://github.com/codefoundry-io/codex-md-improver/actions/runs/37137834714)
passed all five jobs on that exact source. Each macOS job ran278 methods with one
Linux-only skip; each Ubuntu job ran278 with four native-case skips. All four
case-alias checks executed and passed on macOS, and the bytes-name fixture passed
on Ubuntu. Recorded-storage tests passed on all four OS/Python jobs. Python3.10
rejection passed. Native skips are not evidence for the skipped behavior.

All four producers started before verdict consumption and completed. Astra
returned MERGE WITH FIXES with two must-fix findings. Claude returned SAFE TO
MERGE with two Minor findings; Pro and Flash approved without findings. Official
collection was BLOCKED, all entries COMPLETE, none missing; custody and integrity
checks passed. Exact original native output and its observed completed handle
were recorded under owner authorization; hidden runtime identity remains
unexposed. Export manifest:
`a78062911f2e8c1318205ba9010e8ad3e45784a89093cb369ee733fdefcb8535`.
The managed review root was cleaned after export. No vote transfers to new bytes.

## Findings and corrections

| Finding | Disposition |
| --- | --- |
| Astra: whitespace-equivalent reference labels select a later definition or miss a dependency | Accepted. One normalization function casefolds and collapses ASCII spaces, tabs and line endings for definitions and full, collapsed and shortcut uses. First accepted definition still wins. Empty normalized labels do not create dependencies. NBSP and punctuation remain distinct. The existing lexer already admits multiline labels; this does not add a Markdown engine. The [CommonMark0.31.2 matching rule](https://spec.commonmark.org/0.31.2/#matches) was checked2026-10-04. |
| Astra: candidate extraction reads same-byte replacements into excluded SKILL/Git sources | Accepted. Share a canonical source-boundary classifier across graph, candidate and report reads. Retain recorded external Git roots privately on the graph. Recheck before candidate reads, record a precise boundary, clear stale state expansion and identity, and filter candidates to remaining reachable source aliases. Independently reachable descendants survive. Previously captured nodes, hashes and byte counts remain historical observations. |
| Claude: lowercase skill.md falsely excludes a directory, and uppercase requested aliases falsely exclude the ordinary file | Accepted. Use canonical stored file spelling. For a directory, enumerate entries first and recognize only an exact stored SKILL.md regular file. The normal exact-SKILL boundary remains. |
| Claude: malformed persisted frontiers cause AttributeError/exit1 or are silently accepted | Accepted. Validate the optional frontier list and each row's kind/path, with absolute paths for Git administration roots. Reuse validation in report/compare shape checks and direct enrichment. Malformed input returns exit2 without traceback. Existing absent/empty frontiers and blocked rows with error metadata remain valid. |

Two fresh read-only source diagnoses verified these claims before implementation.
The shared boundary classifier does not restrict discovery's permitted Git
pointer/configuration metadata reads. It does not discover additional Git roots,
provide an atomic filesystem snapshot, or reinterpret all Markdown syntax.

## Verification

The root authored bounded private scenarios before changing production source.
A fresh exact codex-md-improver-executor with no inherited turns loaded the
canonical skill and observed RED:19 methods,44 assertion failures, one intended
product AttributeError, zero skips, six passing control methods. Twelve methods
had assertion failures and one errored. The error was direct malformed-frontier
handling, not setup/import failure. Some subcase assertions after a first failure
did not execute; they are not claimed as separately observed RED evidence.

Controls covered ordinary same-byte symlinks, similarly prefixed non-Git paths,
unchanged files, exact-SKILL directory exclusion, valid frontiers, and distinct
punctuation/NBSP labels. Native uppercase/lowercase alias prerequisites actually
executed. All57 source/test and three private scenario fingerprints, Git status
and HEAD remained unchanged; exact fixture cleanup was independently confirmed.

After root implementation, a separate fresh exact executor passed19 focused
methods with no skips,297 full methods with one Linux-only bytes-name skip, and
the skill validator on macOS/Python3.12.13. All five native case-alias tests ran
and passed. All60 source/test fingerprints and Git status remained unchanged;
the disposable fixture was empty, removed and independently absent. The tool
transport truncated part of the verbose full-suite middle, but retained terminal
summaries, the sole skip, validator result and complete final fingerprint map.
Executors wrote only their named disposable fixtures and returned stdout.

Independent scoped Sol source review found no additional concrete defect. It was
read-only and did not claim formal admission or independently execute tests.
Actual copied test PROJECT bindings were verified portable.

Production delta: +63/-14/net49 lines across four runtime modules; total production
Python including the packager is2,434 lines. Three new test files contain240
lines. Documentation is separate. No SKILL.md prompt wording changed.

The local version0.1.0 candidate contains14 selected files plus the embedded
manifest. Archive SHA-256:
`bb54a19f80749a0ab70401aeccde3a29fdf57add4b170f2fdf66acc20e007ab0`.
The corrected commit still needs native CI and a complete fresh four-leg review.
Case-sensitive hosts may skip native alias fixtures; those skips supply no alias
proof. Merge, tag/Release and actual owner installation retain separate gates.
