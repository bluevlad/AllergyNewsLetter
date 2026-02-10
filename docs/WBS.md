# AllergyNewsLetter WBS (Work Breakdown Structure)

> 뉴스레터 시스템 고도화 작업 분해 구조

---

## Phase 1: 경쟁사 동향 분석 + 뉴스 그룹화 (v1.1.0)

**상태**: ✅ 완료 (2026-02-10)

### 1.1 경쟁사 동향 분석 섹션

| # | 작업 | 파일 | 상태 | 비고 |
|---|------|------|:----:|------|
| 1.1.1 | 에스디바이오센서 키워드 추가 | `config/keywords.yaml` | ✅ | type: competitor |
| 1.1.2 | company_types 구성 및 전달 | `src/main.py` | ✅ | generate_and_send_reports, send_newsletter_to_recipient |
| 1.1.3 | _group_by_company() 동향 분석 확장 | `src/reporter/generator.py` | ✅ | type, trend_summary 필드 추가 |
| 1.1.4 | _generate_trend_summary() 구현 | `src/reporter/generator.py` | ✅ | Ollama AI + fallback |
| 1.1.5 | TREND_TARGET_COMPANIES 상수 정의 | `src/reporter/generator.py` | ✅ | 4개 기업 |
| 1.1.6 | stats에 trend_company_count 추가 | `src/reporter/generator.py` | ✅ | |
| 1.1.7 | 경쟁사 동향 분석 HTML 섹션 구현 | `templates/allergy_briefing.html` | ✅ | 고객사 초록/경쟁사 회색 |
| 1.1.8 | 통계 영역 업데이트 | `templates/allergy_briefing.html` | ✅ | 📊 동향분석 N건 |

### 1.2 뉴스 대분류 그룹화

| # | 작업 | 파일 | 상태 | 비고 |
|---|------|------|:----:|------|
| 1.2.1 | NEWS_MEGA_GROUPS 상수 정의 | `src/reporter/generator.py` | ✅ | 의학·연구 / 산업·생활 |
| 1.2.2 | _build_news_groups() 메서드 구현 | `src/reporter/generator.py` | ✅ | 카테고리 → 대분류 매핑 |
| 1.2.3 | generate_daily_report() 연동 | `src/reporter/generator.py` | ✅ | news_groups 변수 전달 |
| 1.2.4 | 대분류 그룹 HTML 섹션 구현 | `templates/allergy_briefing.html` | ✅ | 인라인 카테고리 배지 |

### 1.3 검증

| # | 작업 | 상태 | 비고 |
|---|------|:----:|------|
| 1.3.1 | 뉴스 수집 테스트 | ✅ | 194건 수집 |
| 1.3.2 | 업체동향 수집 테스트 | ✅ | 99건 수집 (에스디바이오센서 25건) |
| 1.3.3 | AI 분석 실행 | ✅ | 293건 분석 (Ollama fallback) |
| 1.3.4 | 테스트 메일 발송 (v1 경쟁사 동향) | ✅ | rainend00@gmail.com |
| 1.3.5 | 테스트 메일 발송 (v2 대분류 그룹) | ✅ | rainend00@gmail.com |

### 1.4 문서화

| # | 작업 | 파일 | 상태 |
|---|------|------|:----:|
| 1.4.1 | WBS 작성 | `docs/WBS.md` | ✅ |
| 1.4.2 | 고도화 이력 문서 | `docs/ENHANCEMENT_LOG.md` | ✅ |

---

## Phase 2: 향후 고도화 계획 (미착수)

| # | 작업 | 설명 | 상태 |
|---|------|------|:----:|
| 2.1 | PubMed 논문 수집 연동 | 논문 섹션 활성화 | ⬜ |
| 2.2 | Ollama 모델 설치 및 AI 요약 고도화 | 동향 요약 품질 향상 | ⬜ |
| 2.3 | 주간 요약 리포트 | 일주일 동향 종합 분석 | ⬜ |
| 2.4 | 수신자별 관심 카테고리 필터링 | 맞춤형 뉴스레터 | ⬜ |
| 2.5 | 경쟁사 뉴스 빈도 트렌드 차트 | 시계열 시각화 | ⬜ |

---
