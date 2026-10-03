# Formal code review R7 and bounded corrections

Reviewed source: `959006dd93cebb993bb8e0240e96b06226ecb136`.
Round: `codex-md-code-20261003-r7`; digest:
`594d9dafd7ca68e371ea80e10dc09ed60f5374f3b54ca7b9a047bf83d533434a`.

Exact-head native CI run `37132809537` succeeded: Ubuntu Python3.11/3.12 each
passed 251 tests, including actual invalid-byte filenames; macOS each passed250
with one Linux-only skip. The Python3.10 rejection guard passed. These observed
tests do not imply all fixture bindings were portable, as this review discovered.

All four actual producers started before verdict consumption and completed.
Astra and Opus requested fixes; Pro and Flash approved without findings. Official
collection was BLOCKED, all entries COMPLETE, none missing. Custody/integrity
checks passed, then evidence was exported and the exact managed root cleaned.
Export manifest: `ec38cddaf6681acdb02ca6476b61ab6b57137ba351720cffe900b655d0eb948a`.
The native original final and actual completed-handle observation were recorded
under existing owner authority; hidden runtime identity remains unexposed. No
vote is converted, and no prior approval transfers to corrected source.

## All three findings

| Claim | Correction |
| --- | --- |
| Literal filesystem percent sequences are URI-decoded and select a readable decoy | Percent-decode original Markdown destinations only. Plain/semantic paths and explicit replacement targets preserve percent sequences. Track explicit replacements separately from syntax so the Markdown default base stays document-relative. Retain existing fragment, filename-line, placeholder, glob and URL conventions. |
| Five R6 tests pin the original host project path | Use the selected test file's repository root. The leader's earlier shell-embedded string replacement silently failed because its matching quotes were removed; an unasserted copy concealed that failure. Direct patches and checked copy assertions now verify actual bindings. Add a structural alternate-file-location check. Canonical test results remain real; earlier portable-binding implications were unwarranted. Published history is retained rather than rewritten or described as never containing the path. |
| A capped route report calls its stream complete | Render explicit cap truncation in both scan and later report rendering; make the scan footer conditional. Keep the complete-stream control. Existing partial JSON/manifest and exit3 remain unchanged. |

The path correction does not add literal hash/colon filename conventions or URI
crawling. A source-bound filesystem target keeps the existing reference suffix
rules. This is a normalization correction within the approved audit population.

## Verification

Exact fresh codex-md-improver-executor instances read canonical source and use
fork_turns=none. They write only the exact disposable fixture and return stdout;
the root retains evidence. The leader alone edits source/tests.

Initial path RED ran eight methods with seven assertion failures, zero errors
and four passing controls. Expanded RED ran11 methods with13 assertion failures,
zero errors and five passing control methods. The failed target/footer assertions
prevented later assertions in those subcases; those later assertions are not
separate RED evidence. The five PROJECT failures are structural portability
checks, not copied-skill execution or distribution admission. Source/private-test
fingerprints, clean Git status and exact fixture cleanup were verified.

Final fresh dedicated GREEN passed37 focused methods (R6+R7) and262 full
methods plus the skill validator on macOS/Python3.12.13. Each suite skipped only
the native-Linux filename fixture; no failures/errors. All53 source/test hashes,
Git status and base HEAD were unchanged. The fixture was empty and independently
confirmed removed. Scoped independent Sol/high source review found no additional
defect. The PROJECT check remains structural evidence; no copied skill is claimed
to have passed the canonical behavior gate.

Production delta: +12/-4/net8 lines in three runtime files; total production
Python including the packager is2,378 lines. New tests150 lines in two files,
plus five one-line fixture-binding replacements. The checked copy helper and
actual source inspection confirmed all seven R6/R7 PROJECT values are relative.
Local version0.1.0 candidate contains14 selected files plus an embedded manifest;
archive SHA-256:
`c539bf5b58ec67db9bdcc172c19defe7e92e7adfeba883bfd002b88711445db2`.

The amended source still requires exact-head native CI and a full fresh four-leg
review. Existing performance and output-volume limits are unchanged.


Final merge, tag/Release and actual owner installation remain separate gates.
