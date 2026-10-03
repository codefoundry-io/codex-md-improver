# codex-md-improver owner decisions

Status: owner requirements ledger. The owner resumed plan review, implementation and pre-merge review on 2026-10-03. Actual installation and final merge remain separate stages.

Questionnaire: `2026-10-03-v1`. Submitted: `2026-10-03T02:35:32.047Z`.
Original attachment SHA-256: `43a1891eec3e2812d34a4dbba57238d10365401ae5abd82f7bb53f7a7cd3024c`.

160 criteria: **107 included, 52 pending, 1 excluded**. Notes are canonical owner text; included notes refine the catalog wording. Pending items are not enabled implicitly.

## Global answers

### purpose

```text
~ 유저 레벨 부터 하위 디렉토리까지 한도 용량 넘는 조합이 있는지 체크
하위로 가야할 지침은 그 프로젝트로 보낼 것
용량 줄이기
조사자료 가이드 등 너무 많은 md를 읽는 레퍼런스 끊기
```

### skillName

```text
codex-md-improver
```

### targets

```text
AGENTS.md, SKILL.md
```

### agentsScope

```text
global-and-project
```

### workflow

```text
plan-undecided
```

### hosts

```text
Mac, Ubuntu
```

### constraints

```text
경로 path로 연결된 모든 파일 조회할 것
상대 경로, 절대 경로 다 지원 해야함
```

### evaluation

```text
owner-review
```

## Subsequent owner direction

- Create a new project directory under `workspace/`.
- Plan a **public** repository at `codefoundry-io/codex-md-improver`.
- Include skill release, distribution, and installation verification in the implementation plan.
- This turn remains planning-only; creating the remote, skill implementation, and installation are execution tasks.

## Later scope corrections — override the original form

- Owner: `AGDNTS.md 는 파일 폴더 트리니까 끝까지 추적해서 각 말단뱔로 용량을 리포팅해야해 알지?` Track the linked file/folder structure to every accessible terminal route and report cumulative bytes per route, with shared-node totals separately.
- Owner: `SKILL은 감사대상 아니야 이건 AGENTS.MD와 관련 링크된 파일들만 평가` Remove standalone SKILL auditing. Evaluate AGENTS.md and its linked files only; a SKILL.md link is recorded as an excluded skill boundary, not expanded into a skill-quality audit. The new tool is still delivered as a Codex skill.
- Owner: `접근 권한 문제가 있으몀 가능한 영영만 검토하는걸로 하자` Permission failure stops only that branch. Continue accessible areas and label blocked frontiers and partial/unknown totals; do not seek broader access automatically.
- The original target list below remains historical input. These later corrections control the implementation plan and supersede its SKILL target entry.

## Execution decisions, 2026-10-03

- Preserve `skills/codex-md-improver/` as the canonical source and expose it through `.agents/skills/codex-md-improver -> ../../skills/codex-md-improver` for repository discovery.
- Resolve analyzer/resources from the loaded skill directory; supply the audited project separately. Default to all accessible scopes of selected projects; current-cwd-only review is explicit.
- Resume with a formal multi-reviewer plan review, then implementation and a pre-merge review. Permit web search for all reviewers, including OpenAI Docs for Codex. Keep Opus 5.5/xhigh, Google Pro/high, Flash/high and Astra/high; configure exact IDs/routes in one JSON file. All enabled legs must approve.
- License: **MIT**, explicitly selected by the owner.
- The owner adopted the structured aggregation contract on 2026-10-03: one PASS/FAIL/NA verdict per rule ID per audit, reject duplicate IDs, applicable=PASS+FAIL, pass-rate=PASS/applicable (undefined at zero), separate NA and unassessed counts, and FAIL-to-PASS transitions only across comparable reports. The legacy parser and other pending criteria remain unadopted.
- For prompt/skill wording plateaus, consolidate findings once with a fresh read-only subagent and apply a bounded revision. Then judge disputed choices through fresh Sol/medium probes with `fork_turns="none"`, without expected answers or review history in worker packets. Dedicated executor and formal approval requirements remain separate.

## Decision register

IDs refer to the questionnaire. These are authoring evidence, not 160 instructions to preload into the shipped skill. Source paths from the local questionnaire are intentionally not included in this prospective public project.

### Included (107)

| ID | Criterion | Owner note | Requested treatment |
| --- | --- | --- | --- |
| AG01 | 지속적으로 유용한 프로젝트 정보 | — | planning |
| AG02 | 전역·저장소·하위 지침 역할 분리 | — | planning |
| AG03 | 실제 적용 지침 파일을 먼저 선택 | — | planning |
| AG04 | override와 fallback 선택 순서 | 파일내 연결된 경로도 볼 것 | planning |
| AG05 | 클라이언트별 적용 범위 구분 | — | planning |
| AG06 | 합산 바이트 한도 검사 | — | planning |
| AG07 | 잘림·누락될 지침 표시 | — | planning |
| AG08 | 전역 사용자 지침 예산 구분 | 전역 지침은 전역에 해당하는 지침만 두고 이를 하위로 내릴지 전역으로 올릴지는 사용자에게 반드시 물을 것 | planning |
| AG09 | 용량 한도와 권장 길이 구분 | 권장 한도의  90%를 위험 상태로 볼 것 | planning |
| AG10 | 참조 문서를 읽는 조건 명시 | 제시한 발동어가 잘 인식될지 직관적이지 않으면 서브에이전트로 평가하는 테스트 존재해야함 | planning |
| AG11 | 규칙의 근거와 적용 범위 | 적용하되 너무 세세한 이유 지침으로 커버되서 이유를 설명할 필요 없는지 구분 할 것 과거 사건에 특히 날짜 이런 것을 넣지 말것 | planning |
| AG12 | 기계적 검사는 실제 도구로 강제 | — | planning |
| AG13 | 모델 업데이트 후 오래된 우회 지침 검토 | 이거 검토할때는 웹 검색을 허용할 것 | planning |
| AG14 | 필요한 검증과 완료 경계 | 전반적인 이 환경의 작업 지침이지 스킬이 되어서는 안됨 해당 항목이 스킬이라면 스킬로 플랜이라면 플랜으로 빠져야 한다고 판단하여 권유할 것 | planning |
| AG15 | 승인 문구를 실제 권한 범위에 맞춤 | 승인이나 지침이 환경설정으로 빠질수 있는 경우 Openaidocs나 웹 검색을 통해서 제안할 것 | planning |
| AG16 | 중단 원인인 지침을 명확히 보고 | — | planning |
| AG19 | 오탐에 따라 리뷰 규칙 조정 | 사용자에게 판단 원인과 대안을 문구를 제시 할 것 | planning |
| AG20 | AGENTS·스킬·메모리·설정 구분 | AGents.md에는 기억이나 과거 원인 조사 자료를 최소화하고 지침만 남길 것 | planning |
| AG22 | 최소 diff와 이유를 먼저 준비 | — | planning |
| AG23 | 문장 정리와 행동 개선 증거 구분 | — | planning |
| C1 | 무엇과 언제의 호출 설명 | — | planning |
| C3 | 입력·행동·출력 중심 | — | planning |
| C4 | 실패 서사와 변명으로 프라이밍하지 않기 | — | planning |
| C5 | 중복과 불필요한 설명 줄이기 | — | planning |
| C6 | 차분하고 직접적인 명령 | — | planning |
| C7 | 불필요한 단계 강제 줄이기 | — | planning |
| C8 | 오래되는 날짜·버전·모델 고정값 | — | planning |
| C9 | 상세는 필요할 때 공개 | references 뿐만 아니라 본문에서 파일이나 폴더를 읽으라고 지시한 모든 항목에 같은 기준을 둬야함. | planning |
| C10 | 긍정적 행동으로 쓰기 | — | planning |
| C11 | 배포 소비자의 언어와 맥락 | — | planning |
| C12 | 도구 설명·타입·식별자·오류 | — | planning |
| C15 | 서로 모순되지 않는 지시 | 모순 되는 지시는 사용자에게 물어서  결정할 것 | planning |
| I01 | 적용 지침의 위치와 범위 | — | planning |
| I02 | 현재 저장소와 내용 대조 | — | planning |
| I03 | 원본 100점 평가표 채택 여부 | 다른 추가 내용들도 종합 평가 기준을 둘 것 | planning |
| I04 | 수정 전 품질 보고서 | — | planning |
| I05 | 파일별 diff와 수정 이유 | — | planning |
| I06 | 작은 변경과 기존 구조 보존 | AGENTS.md  마이그레이션이므로 AGENTs.md 와 이 파일이 링크하는 파일들만 대상 | planning |
| I07 | 명령과 개발 흐름 | — | planning |
| I08 | 필요한 구조 정보 | — | planning |
| I09 | 함정·예외의 이유 | — | planning |
| I10 | 불필요한 설명 축소 | — | planning |
| I11 | 명령·경로·기술의 최신성 | — | planning |
| I12 | 실행 가능한 구체성 | — | planning |
| I13 | 오래된 정보와 복사 흔적 탐지 | — | planning |
| I14 | 필요한 템플릿 섹션만 선택 | — | planning |
| I15 | 저장소 구조에 맞는 배치 | — | planning |
| I16 | 검증된 프로젝트 정보 우선 | — | planning |
| I17 | 일회성 기록과 일반론 제외 | — | planning |
| R01 | 세션에서 부족했던 정보 회수 | — | planning |
| R03 | 반복 가치가 있는 학습만 기록 | — | planning |
| R04 | 학습 추가의 diff와 효용 제시 | — | planning |
| P03 | 삭제는 구체적 근거로 결정 | — | planning |
| P04 | 사용자만 아는 맥락 보존 | — | planning |
| P05 | 확신이 낮으면 보고만 | — | planning |
| P06 | 강조·질책·완곡 표현 검토 | — | planning |
| P07 | 판단 작업의 과도한 단계 강제 검토 | — | planning |
| P08 | 취약한 작업의 정확한 순서 보존 | — | planning |
| P09 | 예시가 만드는 고정 효과 검토 | — | planning |
| P10 | 반복·일반론·예외 누적 검토 | — | planning |
| P11 | 과거 모델의 우회 지침 재검토 | 이때는 웹 검색 허용 | planning |
| P12 | 한 번의 실수를 영구 규칙으로 만들지 않기 | — | planning |
| P13 | 현재 적용 규칙으로 표현 | — | planning |
| P14 | 변동하는 사실은 현재 코드에서 확인 | — | planning |
| P15 | 충돌과 의도한 예외 구분 | — | planning |
| P16 | 최신성을 이유로 권한 약화 금지 | — | planning |
| P17 | 유효한 중복은 오류로 보지 않기 | 의도된 중복인지 사용자에게 물을 것 | planning |
| P18 | 금지문의 실제 이유 확인 | — | planning |
| P19 | 숫자 강제의 필요성 검토 | — | planning |
| P20 | 지적별 근거와 확신 기록 | — | planning |
| P21 | 선택 가능한 개별 diff | — | planning |
| P22 | 목적은 간결한 재작성으로 보존 | — | planning |
| P23 | 행동 확인과 자기평가 구분 | 서브에이전트에서 인식하는지 fresh eye로 확인할 것 낮은 모델로 확인 할 것 | planning |
| P24 | 회귀가 있으면 필요한 규칙 복원 | — | planning |
| P25 | 정확한 문자열에 의존하는 소비자 확인 | — | planning |
| AA1 | 작성 대화를 가리키는 잔여 표현 | — | planning |
| AA2 | 대화식 인사·자기 설명·사과 제거 | — | planning |
| AA3 | 약한 완곡어 대신 직접 지시 | — | planning |
| AA4 | 구체적인 사실을 발명하지 않기 | 웹 검색 허용 | planning |
| AA5 | 기능적 서식만 남기기 | — | planning |
| AA6 | 본문도 소비자의 언어로 | — | planning |
| L-C8-BODY-DATE | 본문 날짜 후보 | — | planning |
| L-C8-BODY-YEAR | 본문 시간 문구 근처 연도 후보 | — | planning |
| L-C8-BODY-SEMVER | 본문 세 부분 버전 후보 | — | planning |
| L-C8-BODY-TOOLVER | 본문 도구·런타임 버전 후보 | — | planning |
| L-C8-BODY-MODEL | 본문 모델명·코드명 후보 | — | planning |
| L-C8-BODY-RECENCY | 본문 출시의 최근성 문구 후보 | — | planning |
| L-C6 | C6 imperative density | — | planning |
| L-C4-EXCUSES | C4 enumerated excuses | — | planning |
| L-C4-NARRATIVE | C4 failure narrative | — | planning |
| L-C10 | C10 negation density | — | planning |
| L-C9-TOC | C9 reference TOC | — | planning |
| L-C3 | C3 world-facts (assist) | — | planning |
| L-AA1 | AA1 authoring-conversation carryover | — | planning |
| L-AA2 | AA2 chat-register padding | — | planning |
| L-AA3 | AA3 sycophantic softeners | — | planning |
| L-AA5 | AA5 decoration overload | — | planning |
| L-AA6 | AA6 body language | — | planning |
| L-REPORT | 후보 출력·줄 번호·종료 코드 | — | planning |
| L-SEMANTIC | 자동 탐지와 의미 증거 분리 | — | planning |
| L-SCORE-DELTA | 전후 변화의 결정적 집계 | — | planning |
| U01 | AGENTS.md와 SKILL.md를 별도 대상으로 취급 | — | planning |
| U02 | 정적 검사와 행동 검증을 구분 | 서브에이전트로 인식가능한지 여부 확인 | planning |
| U03 | fresh-eye 행동 실험은 별도 범위 | 저렴한 서브에이전트로 인식 여부만 할수 있는 방법 마련하자 | model |
| U04 | 표현 논쟁의 반복을 막기 | 문법 모호한 표현 논쟁 금지 직접 확인해볼 것 | planning |
| U05 | 구체적 환경과 실행 설정 보존 | — | planning |
| U06 | 중복은 관련 근거로 합치기 | — | planning |

### Pending — not adopted (52)

| ID | Criterion | Owner note | Requested treatment |
| --- | --- | --- | --- |
| AG17 | 저장소별 중요한 리뷰 규칙 | — | planning |
| AG18 | 지속 규칙과 일회성 리뷰 초점 분리 | — | planning |
| AG21 | 활성 지침을 새 세션에서 확인 | — | planning |
| C0 | frontmatter 등록 구조 | — | planning |
| C2 | 하나의 일 | — | planning |
| C13 | 비가역적 행동의 승인·정지 조건 | — | planning |
| C14 | 긴 자료 뒤에 질문 배치 | — | planning |
| C16 | CLI 호출·프롬프트 주입 분리 | — | planning |
| R02 | 공유 정보와 개인 정보 위치 구분 | — | planning |
| P01 | 대상 파일·모델·가정 명시 | — | planning |
| P02 | 지침이 생긴 이유 확인 | — | planning |
| P26 | 대상 모델이 바뀌면 재감사 | — | planning |
| O1 | 추론 노력은 작업에 맞게 | — | planning |
| O2 | 출력 길이와 형식을 별도로 | — | planning |
| O3 | 추론 모델에 단순하고 직접적인 지시 | — | planning |
| O4 | 결과·성공 조건 중심 | — | planning |
| O5 | API 도구와 SKILL 도구 설명 구분 | — | planning |
| O6 | 릴리스명 대신 현재 기능 계약 검증 | — | planning |
| A1 | Claude SKILL frontmatter 규격 | — | planning |
| A2 | Claude SKILL은 개요와 주문형 자료 | — | planning |
| A3 | 취약성에 맞는 자유도 | — | planning |
| A4 | effort·thinking과 내부 추론 출력 | — | planning |
| A5 | XML·역할·긍정 예시·안정 캐시 | — | planning |
| A6 | 구형 과잉 scaffolding 정리 | — | planning |
| A7 | 새 담당자에게 설명하듯 도구 문서화 | — | planning |
| G1 | 샘플러 설정의 API 범위 | — | planning |
| G2 | thinking은 목표량이 아닌 상한 | — | planning |
| G3 | 끝의 제약과 명시적 길이 요구 | — | planning |
| G4 | 최근 사실·계산은 도구와 날짜로 | — | planning |
| G5 | 함수명과 선별 도구 집합 | — | planning |
| G6 | 추론·추측 전면 금지 대신 근거 규칙 | — | planning |
| L-C0 | C0 frontmatter loads | — | planning |
| L-C8-DESC-DATE | description 날짜 후보 | — | planning |
| L-C8-DESC-YEAR | description 시간 문구 근처 연도 후보 | — | planning |
| L-C8-DESC-SEMVER | description 세 부분 버전 후보 | — | planning |
| L-C8-DESC-TOOLVER | description 도구·런타임 버전 후보 | — | planning |
| L-C8-DESC-MODEL | description 모델명·코드명 후보 | — | planning |
| L-C8-DESC-RECENCY | description 출시의 최근성 문구 후보 | — | planning |
| L-C9-BODY | C9 body length | — | planning |
| L-C11 | C11 description language | — | planning |
| L-KIND | 파일 유형 선택 | — | planning |
| L-QUOTING | 인용 예시 제외의 한계 | — | planning |
| L-THRESHOLDS | 밀도·길이의 소프트 기본값 | — | planning |
| L-SCORE-PARSE | 집계 입력 형식 | — | planning |
| L-SCORE-FAIL-WINS | 중복 기준은 FAIL 우선 | — | planning |
| L-SCORE-TALLY | 적용 기준·통과율 산식 | — | planning |
| L-SCORE-RESIDUAL | 모든 FAIL을 통과율 앞에 | — | planning |
| L-SCORE-NO-ORACLE | 품질 점수·의미 판정 기능 없음 | — | planning |
| L-SCORE-COVERAGE | 보고서 누락·ID 검증 한계 | — | planning |
| L-SCORE-CLI | score CLI 계약 | — | planning |
| U07 | 운영체제별 검증 범위 | — | planning |
| U08 | 근거 수준을 결과에 표시 | — | planning |

### Excluded — do not implement (1)

| ID | Criterion | Owner note | Requested treatment |
| --- | --- | --- | --- |
| AG24 | 초기 생성본을 저장소에 맞게 편집 | — | planning |

## Selected interpretation boundaries

- `I06` and the later scope correction limit both target auditing and migration to AGENTS.md and its linked files. Standalone SKILL auditing has been removed.
- `U03`, `P23`, `U02`, and `AG10` notes request narrow independent recognition probes; they do not authorize broad performance experiments.
- `I03` includes the subjective 100-point rubric. Additional assessment dimensions need a transparent mapping, not an invented vendor score.
- `L-SCORE-DELTA` requests before/after findings; the legacy parser and other pending score criteria remain unadopted.
- `AG24` excludes the `/init`-based seed-and-edit workflow. Creating the new project's own authored development instructions later is a packaging concern, not that audit workflow.
