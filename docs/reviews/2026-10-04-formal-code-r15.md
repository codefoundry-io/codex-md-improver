# Formal code review R15 and locale correction

Reviewed source: `cdb54cb90b4fb9996570c2ad234d511680dce365`.
Round: `codex-md-code-20261003-r15`; digest:
`b81c939b58fdad61a05c3760cfe66af01dc104ae2b50d5c217899e313b5ab237`.

[Exact-source CI run37154363232](https://github.com/codefoundry-io/codex-md-improver/actions/runs/37154363232)
passed all five jobs. Each macOS job ran417 methods with415 passes/two skips;
each Ubuntu job had396 passes/21 native-alias skips. All21 native aliases ran on
macOS, Linux bytes-name/distinct-case controls ran on Ubuntu, and the Python3.10
guard passed. This evidence did not cover the remaining locale-dependent input.

All four producers started before verdict consumption and completed. Every leg
explicitly returned SAFE TO MERGE, with no open questions. Astra, Pro and Flash
reported no findings; Claude reported one Minor. Official collection was AGREED,
all four COMPLETE, no missing entry or selection deviation. Every leg had web
permission. The actual native original and completed handle were retained;
hidden runtime identity remains unexposed. Export and exact cleanup succeeded:
`a79770a11bfa938bf832d9e3faef56859e704dace46ccba242b2fb0e96c54ddc`.

That admission applies to the reviewed source. The following correction changes
its bytes and therefore requires its own complete review before merge.

## Minor disposition

The scan command used locale-default text decoding for settings and resolutions
JSON, whereas report/compare decoded JSON from bytes. Under a single-byte
non-UTF-8 locale, UTF-8 path keys can become different but syntactically valid
strings. A supplied untrusted gate or declared base can then miss silently;
explicit resolution bindings can fail. The input contract has no UTF-8-locale
restriction.

Independent read-only diagnosis confirmed the actual host precondition on
macOS/Python3.12.13: en_US.ISO8859-1 is available, preferred text encoding is
ISO8859-1, UTF-8 mode is0 and filesystem encoding remainsUTF-8. This metadata
check was not a behavioral test; Ubuntu locale availability was not assumed.

The accepted correction reads both JSON inputs from bytes, using the existing
JSON decoder behavior already used by report/compare. It needs two replaced
lines in md_improver.py, no new helper or package resource. No prompt wording,
loader semantics or approval boundary changes.

## Verification

A fresh exact codex-md-improver-executor loaded canonical SKILL.md with no
inherited turns and ran the four private methods once before production edits.
Three methods failed, the UTF-8 control passed all three equivalent subchecks,
and there were zero errors or skips. All three native Latin-1 guards passed:
preferred codec ISO-8859-1, UTF-8 mode0, UTF-8 filesystem encoding and single-byte
decoding. Console encoding was isolated from default file decoding.

The trust case first failed with unset instead of untrusted; its later trust-key,
byte-gate and loader-outcome assertions were not reached. The declared-base case
returned3; the resolution case returned2 with a source/scenario binding error.
Their later audit and terminal-route assertions were not reached. All80 source/test
fingerprints, private test, HEAD/clean status and separate harness/packager hashes
were preserved. Actual terminal exit was1. The exact fixture was empty, removed
and independently absent. No behavioral rerun was used for clipped output.

Root then applied the two replacements and copied one portable regression file:
production +2/-2/net0, tests161 lines/four methods, documentation counted separately.
SKILL.md wording and the15-resource distribution boundary remain unchanged.

Fresh exact GREEN passed all four focused methods and421 full methods (419 passes,
two platform skips), plus the skill validator. All native Latin-1 guards and
downstream trust/key/zero-byte gate, declared-base and resolution-route assertions
passed in both focused and full runs. The UTF-8 control passed. The tests verify
the codec and runtime properties but do not emit the selected locale's name.

The full suite passed all10 distribution tests and all five native package tests.
The skips were the Linux bytes-name fixture and the distinct case-sensitive sibling
control unavailable on this macOS volume. All81 source/test fingerprints, HEAD/status
and separate harness/packager hashes matched before and after. Actual session5925
reached terminal exit0; all three harness commands returned0. Original returned
output was retained without rerun, and exact cleanup was independently confirmed.

A fresh Sol/medium source review found no actionable scoped defect and preserved
both file hashes and Git status. It did not execute tests or candidate code. Root
checked those exact hashes and the packager hash before building the candidate.
The executor's initial no-match memory search interrupted a chained skill read;
canonical SKILL.md was subsequently read before execution. That operator issue
did not affect the test.

The local0.1.0 candidate contains15 resources plus its manifest, SHA256:

`cc0cb7c3bc484e684ebba1ca2056ad37d9f868a09d6fbc4c0ab986b420b5ccbd`.

This candidate is not a release or installation.

The corrected commit still requires exact-head native CI and a fresh complete
four-leg review. R15 admission does not transfer to changed source. Final merge,
tag/Release and actual owner installation remain separate owner approvals.
