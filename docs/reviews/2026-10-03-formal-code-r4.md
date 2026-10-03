# Formal code review R4 and bounded corrections

Reviewed source: `979eda8d00fb8adc882ffa9f4725fa2f01913dfd`.
Round: `codex-md-code-20261003-r4`; content digest:
`30ea9de0dfbd989af3b06a44503121b9c7cdc10715de450b7682268f92cf9d1e`.

The exact source passed native CI run `37123465081`: macOS and Ubuntu on Python
3.11/3.12 each passed 182 tests, and the Python 3.10 rejection guard passed.
All four selected producers started on one bound packet before results were
consumed. Opus and Astra requested fixes; Pro and Flash approved. Official
collection was BLOCKED, with all selected entries COMPLETE and no missing leg.
Source, toolkit, prompts and custody bindings remained intact. All writers ended
before export and exact cleanup. Export manifest:
`699f2c348ac24244a477cf2264fcfbc4be27f19122274495c31f6d0c1692b5c0`.

Pro's first attempt ended in a vendor ERROR from a malformed empty function call,
without a verdict. The official recorder classified it FAILED_TO_RUN. Its
same-basis second attempt retained route/model/effort and completed SAFE TO MERGE;
the original failure and diagnosis remain preserved. This was a transport retry,
not replacement of a completed negative vote. Actual native final text and the
host-observed completed handle were recorded unchanged under owner authorization;
unexposed effective model/effort remain null. These are custody observations,
not signed runtime attestation.

## Findings and dispositions

Opus reported five findings and Astra three, with two overlaps: six distinct claims.

| Claim | Disposition |
| --- | --- |
| Git metadata bypasses sensitive identity checks | Pass the same initialized protected reader through inventory and trust lookup, including `.git`, worktree `gitdir` and `commondir` reads. Preserve existing regular-file, symlink and 64KiB metadata rules. |
| Configuration can open FIFOs/devices | Reject nonregular sources in the shared reader before cache access or byte reads. Existing configuration error handling records uncertainty and retains accessible guidance. |
| Inline link titles become filenames | Scan balanced destinations and complete optional titles independently, retaining exact source spans for angle/bare destinations and all three title delimiters. Use the same nonoverlapping spans for context classification so title data cannot become dependencies or erase outside directives. |
| Plain/autolink URLs become local frontiers | Inventory URL spans before plain-path extraction; classify URL and anchor targets before the local read/uncertain gate. Do not crawl them. Local ambiguous references remain partial. |
| Graph materialization repeats shared paths | Verified static performance limitation, retained as Minor and deferred. `--max-routes` caps route enumeration, not graph-build time. Context-dependent cached revisits also repair alias-cycle states; removing them unconditionally loses legitimate relative descendants. This correction does not claim bounded graph complexity. |
| Korean particles become part of a plain path | Do not impose ASCII-only extensions: the exact Unicode-suffixed name can be a real distinct file. A controlled example demonstrates the existing source/hash/span-bound resolution to the intended path, while a second control preserves the legitimate Unicode filename. The initial ambiguity remains partial until resolved; no automatic suffix-stripping claim is made. |

The four corrections close existing privacy, special-file and reference contracts.
They add no generic secret detector, Markdown framework or new audit population.
Filesystem path/stat checks do not promise atomic race-free security against an
adversarial concurrent replacement; known-source protection is a bounded contract.

## Dedicated verification

Fresh exact `codex-md-improver-executor` instances used canonical source and no
inherited conversation. The leader alone edited source and tests.

- Initial RED: seven methods, 23 assertion failures, zero errors; both parser
  controls passed. Synthetic protected identities and special-file cases failed
  at patched byte-read boundaries, without opening real credentials or devices.
- URL RED: four methods, 13 assertion failures, zero errors. Local-uncertainty,
  existing Markdown URI, Unicode filename and semantic-resolution controls passed.
- Scoped review found adjacent delimiter and URL-punctuation failures: a fresh
  RED produced 21 assertion failures across three methods, zero errors, with two
  controls passing. The leader preserved balanced destinations, complete titles
  and balanced URL closing punctuation.
- A title-word classification leak received its own RED: four assertion failures,
  zero errors, while the prior three methods passed. Reusing the inline span
  parser closed that leak. Scoped rereview then found an introduced overlap bug
  that erased outside `Example.` context; a fresh RED produced two failing
  subcases and a passing adjacent-links control. A four-line consumed-span guard
  closed it, and the final scoped read-only rereview was clean.
- Intermediate GREEN results of 193 and 197 tests remain historical evidence.
  Final fresh GREEN passed 17 focused / 199 full tests and the skill validator on
  native macOS/Python 3.12.13. All canonical-source/test fingerprints and Git status
  were unchanged; every exact fixture was empty and removed.

The bounded source rereview closes the checked corrections, not the formal gate.
No SKILL.md or choice-probe prompt changed in R4, so no vocabulary revision or
additional model-choice experiment was substituted for runtime evidence.

Corrected local version-0.1.0 candidate ZIP SHA-256:
`715dcf93027d3d4b7253c2564e9327eee7cf2d4ae787b2e5028ec20f0aa2854b`.
It contains the selected 14 files plus embedded manifest; it is not a release or
installed-discovery result. No code admission, merge, tag/Release or owner
installation has been claimed. The corrected commit needs its own native CI and
a fresh full four-leg code review; no earlier vote transfers.
