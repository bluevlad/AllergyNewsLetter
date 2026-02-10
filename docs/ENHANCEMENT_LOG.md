# AllergyNewsLetter 고도화 이력

> 뉴스레터 시스템의 기능 고도화 내용을 기록합니다.

---

## v1.1.0 — 경쟁사 동향 분석 섹션 + 뉴스 대분류 그룹화

**작업일**: 2026-02-10
**브랜치**: prod

### 배경

- 기존 "🏢 업체 동향" 섹션이 단순 뉴스 나열에 그쳐 분석 가치가 낮음
- 카테고리별 뉴스(임상/치료, 연구/학술 등 6개)가 각각 독립 섹션으로 나열되어 스크롤이 길고 집중도 저하

### 변경 내용

#### 1단계: 경쟁사 동향 분석 섹션 신설

| 항목 | 상세 |
|------|------|
| **대상 기업** | 수젠텍(고객사), 에스디바이오센서, 바디텍메드, 프로테옴텍 |
| **신규 키워드** | 에스디바이오센서, SD바이오센서, SD Biosensor 등 |
| **동향 요약** | Ollama AI 1줄 요약 (fallback: 최상위 기사 summary) |
| **UI 구분** | 고객사=초록 배지(#2e7d32), 경쟁사=회색 배지(#546e7a) |

#### 2단계: 뉴스 대분류 그룹화

| 항목 | 상세 |
|------|------|
| **기존** | 6개 카테고리 × 독립 섹션 (📌 반복) |
| **변경** | 2개 대분류 그룹으로 통합 |
| **🔬 의학·연구 소식** | 임상/치료 + 연구/학술 |
| **📋 산업·생활 소식** | 생활/관리 + 산업/시장 + 규제/정책 + 기타 |
| **카테고리 표시** | 인라인 배지로 각 기사 옆에 표시 |
| **정렬** | 그룹 내 중요도 순 |

### 수정 파일

| 파일 | 변경 내용 |
|------|----------|
| `config/keywords.yaml` | 에스디바이오센서 키워드 추가 (type: competitor) |
| `src/main.py` | company_types dict 구성 → generator에 전달 |
| `src/reporter/generator.py` | `_group_by_company()` 동향 분석 확장, `_generate_trend_summary()` 신규, `_build_news_groups()` 대분류 그룹화, `NEWS_MEGA_GROUPS` 상수 |
| `templates/allergy_briefing.html` | 경쟁사 동향 분석 UI, 대분류 그룹 UI, 통계 영역 변경 |

### 변경하지 않은 파일

- `src/collector/base.py`, `src/collector/naver_news.py` — 기존 수집 로직 그대로 동작
- `src/database/models.py`, `src/database/repository.py` — company 필드 이미 존재
- `src/processor/summarizer.py` — generator에서 직접 Ollama 호출

---
