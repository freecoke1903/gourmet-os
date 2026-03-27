"""
Gourmet-OS v3 · Mobile-First
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
모바일 최적화 · @st.dialog 상세 · AND 다중필터 · LLM 지연로딩
"""

import re
import textwrap

import pandas as pd
import streamlit as st

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 0. 설정
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 우선순위: st.secrets > 하드코딩 > 런타임 입력
def _get_csv_url() -> str:
    try:
        return st.secrets["SHEET_CSV_URL"]
    except Exception:
        return ""

# ★ 하드코딩하려면 여기에 URL을 넣으세요
SHEET_CSV_URL: str = _get_csv_url() or ""

def _get_llm_config() -> tuple[str, str]:
    """API 키 우선순위: st.secrets > session_state(UI 입력) > 빈 값."""
    try:
        key = st.secrets.get("LLM_API_KEY", "")
        provider = st.secrets.get("LLM_PROVIDER", "openai")
        if key:
            return key, provider
    except Exception:
        pass
    return (
        st.session_state.get("llm_api_key", ""),
        st.session_state.get("llm_provider", "openai"),
    )

REQUIRED_COLUMNS = [
    "메뉴명", "만족도", "분류", "건강",
    "소요 시간", "핵심 식재료", "부재료/소스", "조리법 (통합)",
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. 모바일 퍼스트 CSS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MOBILE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');

:root {
    --bg: #f7f6f3;
    --surface: #ffffff;
    --border: #e5e2db;
    --border-hover: #c5c2bb;
    --text-primary: #1a1a1a;
    --text-secondary: #666;
    --text-muted: #999;
    --accent: #2d2d2d;
    --tag-time-bg: #f0efe9; --tag-time-fg: #555;
    --tag-cat-bg: #e8f4e8; --tag-cat-fg: #2d6a2d;
    --tag-health-bg: #e8eef8; --tag-health-fg: #2d4a8a;
    --tag-sat-bg: #fff8e8; --tag-sat-fg: #8a6a2d;
}

.stApp { font-family: 'Noto Sans KR', sans-serif; background: var(--bg); }

/* ── 메인 컨테이너 폭 제한 (모바일 가독성) ── */
.block-container {
    max-width: 640px !important;
    padding: 1rem 1rem 4rem !important;
}

/* ── 헤더 ── */
.app-header {
    text-align: center;
    padding: 0.8rem 0 0.5rem;
    border-bottom: 2px solid var(--accent);
    margin-bottom: 1rem;
}
.app-header h1 { font-size: 1.3rem; font-weight: 700; color: var(--text-primary); margin: 0; }
.app-header p { font-size: 0.75rem; color: var(--text-muted); margin: 0.15rem 0 0; font-weight: 300; }

/* ── 결과 바 ── */
.result-bar {
    display: flex; justify-content: space-between; align-items: center;
    padding: 0.4rem 0; margin-bottom: 0.5rem;
}
.result-count { font-size: 0.8rem; color: var(--text-secondary); }
.sort-label { font-size: 0.75rem; color: var(--text-muted); }

/* ── 메뉴 카드 ── */
.m-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.9rem 1rem;
    margin-bottom: 0.55rem;
    transition: border-color 0.12s, box-shadow 0.12s;
    -webkit-tap-highlight-color: transparent;
}
.m-card:active { border-color: var(--accent); box-shadow: 0 1px 8px rgba(0,0,0,0.06); }
.m-card-title {
    font-size: 0.95rem; font-weight: 600; color: var(--text-primary);
    margin-bottom: 0.4rem; line-height: 1.35;
}
.m-card-tags { display: flex; flex-wrap: wrap; gap: 0.35rem; margin-bottom: 0.35rem; }
.tag {
    display: inline-block; font-size: 0.68rem; padding: 0.12rem 0.5rem;
    border-radius: 20px; font-weight: 400; white-space: nowrap;
}
.tag-time { background: var(--tag-time-bg); color: var(--tag-time-fg); }
.tag-cat { background: var(--tag-cat-bg); color: var(--tag-cat-fg); }
.tag-health { background: var(--tag-health-bg); color: var(--tag-health-fg); }
.tag-sat { background: var(--tag-sat-bg); color: var(--tag-sat-fg); }
.m-card-ing { font-size: 0.75rem; color: var(--text-muted); line-height: 1.5; }

/* ── 모달(dialog) 내부 스타일 ── */
.d-meta { display: flex; flex-wrap: wrap; gap: 0.4rem; margin: 0.6rem 0; }
.d-divider { height: 1px; background: var(--border); margin: 0.8rem 0; }
.d-section-title { font-size: 0.82rem; font-weight: 600; color: var(--text-secondary); margin-bottom: 0.35rem; }
.d-ing-list { list-style: none; padding: 0; margin: 0 0 0.2rem; }
.d-ing-list li { font-size: 0.82rem; color: var(--text-secondary); padding: 0.1rem 0; }
.d-ing-list li::before { content: "· "; color: var(--text-muted); }
.step-box {
    background: var(--bg); border-left: 3px solid var(--border);
    padding: 0.65rem 0.8rem; margin: 0.45rem 0; border-radius: 0 6px 6px 0;
    font-size: 0.88rem; line-height: 1.7; color: #333;
}
.step-num { font-weight: 700; color: var(--text-primary); margin-right: 0.3rem; }

/* ── 빈 상태 ── */
.empty-state { text-align: center; padding: 2.5rem 1rem; color: var(--text-muted); }
.empty-state .icon { font-size: 2.2rem; margin-bottom: 0.4rem; }
.empty-state p { font-size: 0.88rem; }

/* ── Streamlit 위젯 오버라이드 ── */
div[data-testid="stExpander"] details { border: 1px solid var(--border) !important; border-radius: 8px !important; }
div[data-testid="stExpander"] summary { font-size: 0.82rem !important; }
button[kind="secondary"] { font-size: 0.82rem !important; }

/* ── 필터 영역 칩 스타일 ── */
.filter-summary {
    font-size: 0.75rem; color: var(--text-muted);
    padding: 0.3rem 0; line-height: 1.6;
}
.filter-chip {
    display: inline-block; background: var(--accent); color: #fff;
    font-size: 0.68rem; padding: 0.1rem 0.5rem; border-radius: 12px; margin-right: 0.3rem;
}

/* ── 사이드바 완전 숨김 ── */
section[data-testid="stSidebar"] { display: none !important; }
button[data-testid="stSidebarCollapsedControl"] { display: none !important; }
</style>
"""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. 데이터 로드 (TTL 캐시)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@st.cache_data(ttl=3600, show_spinner=False)
def load_data(csv_url: str) -> pd.DataFrame:
    df = pd.read_csv(csv_url)
    df.columns = [c.strip() for c in df.columns]
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        st.error(f"CSV에 다음 컬럼이 없습니다: {missing}")
        st.stop()
    df["_분"] = df["소요 시간"].apply(_parse_minutes)
    df["_만족도"] = pd.to_numeric(df["만족도"], errors="coerce").fillna(0)
    return df


def _parse_minutes(raw) -> int:
    if pd.isna(raw):
        return 9999
    s = str(raw).strip()
    h = re.findall(r"(\d+)\s*[시h]", s)
    m = re.findall(r"(\d+)\s*[분m]", s)
    t = int(h[0]) * 60 if h else 0
    t += int(m[0]) if m else 0
    if t == 0:
        d = re.findall(r"\d+", s)
        t = int(d[0]) if d else 9999
    return t


def _unique_values(series: pd.Series, sep: str = ",") -> list[str]:
    """시리즈에서 sep으로 분리 후 고유값 정렬 리스트."""
    return sorted({
        v.strip() for raw in series.dropna()
        for v in str(raw).split(sep) if v.strip()
    })


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. 필터링 엔진 (독립 AND 조건)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def apply_filters(
    df: pd.DataFrame,
    max_minutes: int | None,
    ingredient: str,
    health_goal: str,
    categories: list[str],
    sort_by: str,
) -> pd.DataFrame:
    """모든 필터를 AND로 결합하여 적용 후 정렬."""
    out = df.copy()

    if max_minutes is not None:
        out = out[out["_분"] <= max_minutes]

    if ingredient:
        # ★ 핵심 식재료 컬럼에서만 검색 (부재료 배제)
        out = out[out["핵심 식재료"].fillna("").str.contains(
            ingredient.strip(), case=False, regex=False
        )]

    if health_goal:
        out = out[out["건강"].fillna("").str.contains(
            health_goal.strip(), case=False, regex=False
        )]

    if categories:
        out = out[out["분류"].fillna("").apply(
            lambda x: any(c in str(x) for c in categories)
        )]

    # 정렬
    if sort_by == "빠른 순":
        out = out.sort_values("_분", ascending=True)
    elif sort_by == "만족도 순":
        out = out.sort_values("_만족도", ascending=False)

    return out


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. AI 가이드 (캐싱 + 지연 로딩)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

GOURMET_SYSTEM_PROMPT = textwrap.dedent("""\
    당신은 **Gourmet-OS 분석 엔진**입니다.
    역할: 가정식 조리 과정의 각 단계를 물리·화학·생리학적 관점에서 해설하는 전문 분석관.

    ── 페르소나 규칙 ──
    1. 톤: 객관적, 분석적, 과학적. 감탄사·이모지·수사적 표현 금지.
    2. 깊이: 단순 지시가 아니라 **왜 그래야 하는지**
       물리/화학/생리학적 이유를 반드시 포함.
       - 열전달: 마이야르 반응(140-165 °C), 캐러멜화(160 °C+),
         전분 호화(60-80 °C) 등.
       - 식감: 콜라겐→젤라틴 전환(75 °C↑), 글루텐 네트워크 등.
       - 영양: 지용성 비타민 흡수, 비타민C 열분해 최소화 등.
       - 풍미: 알리신 생성, 캡사이신 지용성, 글루탐산 시너지 등.
    3. 분량: 단계당 3-5문장. 핵심 수치(온도, 시간, pH) 1개 이상 포함.
    4. 안전: 고온·날것·알레르기 해당 시 간결히 명시.
    5. 언어: 한국어(과학 용어 영문 병기).

    ── 응답 형식 ──
    [단계 N 분석]
    • 핵심 원리: (1-2문장)
    • 최적 조건: 온도·시간·비율 등
    • 실패 시나리오: 조건 이탈 시 결과
    • 팁: 가정 환경 대안 (선택)
""")


@st.cache_data(ttl=86400, show_spinner=False)
def _cached_llm_call(recipe_step: str, menu_name: str, provider: str, api_key: str) -> str:
    """LLM 호출 결과를 24시간 캐싱. 동일 (단계, 메뉴)엔 재호출 없음."""
    user_msg = (
        f"메뉴: {menu_name}\n"
        f"아래 조리 단계를 Gourmet-OS 분석 엔진 페르소나로 해설하라.\n\n"
        f"조리 단계:\n{recipe_step}"
    )

    if provider == "openai":
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": GOURMET_SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.3, max_tokens=800,
            )
            return resp.choices[0].message.content
        except Exception as e:
            return f"⚠️ OpenAI 호출 실패: {e}"

    if provider == "gemini":
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                "gemini-1.5-flash", system_instruction=GOURMET_SYSTEM_PROMPT,
            )
            return model.generate_content(user_msg).text
        except Exception as e:
            return f"⚠️ Gemini 호출 실패: {e}"

    return ""


def get_analysis(step: str, menu: str) -> str:
    """지연 로딩 래퍼. API 키 없으면 안내 반환."""
    api_key, provider = _get_llm_config()
    if not api_key:
        return (
            "`LLM_API_KEY` 미설정 — 키를 넣으면 이 영역에 "
            "물리·화학·생리학 기반 단계별 해설이 생성됩니다."
        )
    return _cached_llm_call(step, menu, provider, api_key)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. 조리법 파싱
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def split_steps(text: str) -> list[str]:
    if not text or text.strip() in ("", "nan"):
        return []
    parts = re.split(r"\n\s*(?:\d+[.)]\s*|[①-⑳]\s*)", text)
    parts = [s.strip() for s in parts if s.strip()]
    if len(parts) >= 2:
        return parts
    lines = [ln.strip().lstrip("-•·").strip() for ln in text.split("\n") if ln.strip()]
    if len(lines) >= 2:
        return lines
    sents = [s.strip() for s in re.split(r"[.。]\s+", text) if s.strip()]
    return sents if len(sents) >= 2 else [text.strip()]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. UI — 상세 모달 (@st.dialog)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@st.dialog("📋 레시피 상세", width="large")
def show_detail(menu_name: str, df_full: pd.DataFrame):
    """
    원본 df에서 메뉴를 조회 → 필터 상태와 무관하게 안정적으로 표시.
    LLM 분석은 사용자가 expander를 열 때만 실행 (지연 로딩).
    """
    match = df_full[df_full["메뉴명"] == menu_name]
    if match.empty:
        st.error("메뉴를 찾을 수 없습니다.")
        return

    row = match.iloc[0]

    # ── 메타 태그 ──
    tags = []
    for val, cls in [
        (row.get("소요 시간"), "tag-time"),
        (row.get("분류"), "tag-cat"),
        (row.get("건강"), "tag-health"),
    ]:
        v = str(val) if pd.notna(val) else ""
        if v:
            tags.append(f'<span class="tag {cls}">{v}</span>')
    sat = str(row.get("만족도", ""))
    if sat and sat != "nan":
        tags.append(f'<span class="tag tag-sat">만족도 {sat}</span>')

    st.markdown(f'<div class="d-meta">{"".join(tags)}</div>', unsafe_allow_html=True)

    # ── 식재료 ──
    st.markdown('<div class="d-divider"></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        core = [i.strip() for i in str(row.get("핵심 식재료", "")).split(",") if i.strip()]
        if core:
            items = "".join(f"<li>{i}</li>" for i in core)
            st.markdown(
                f'<div class="d-section-title">핵심 식재료</div>'
                f'<ul class="d-ing-list">{items}</ul>',
                unsafe_allow_html=True,
            )
    with c2:
        sub = [i.strip() for i in str(row.get("부재료/소스", "")).split(",") if i.strip()]
        if sub:
            items = "".join(f"<li>{i}</li>" for i in sub)
            st.markdown(
                f'<div class="d-section-title">부재료 / 소스</div>'
                f'<ul class="d-ing-list">{items}</ul>',
                unsafe_allow_html=True,
            )

    # ── 조리법 ──
    st.markdown('<div class="d-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="d-section-title">조리법</div>', unsafe_allow_html=True)

    steps = split_steps(str(row.get("조리법 (통합)", "")))
    if not steps:
        st.info("조리법 데이터가 비어 있습니다.")
        return

    for i, step in enumerate(steps, 1):
        st.markdown(
            f'<div class="step-box"><span class="step-num">{i}</span>{step}</div>',
            unsafe_allow_html=True,
        )
        # ★ 지연 로딩: expander 열 때만 LLM 호출
        with st.expander("🔬 과학적 분석 보기", expanded=False):
            if st.button(f"분석 실행", key=f"llm_{menu_name}_{i}"):
                with st.spinner("분석 중…"):
                    result = get_analysis(step, menu_name)
                st.markdown(result)
            else:
                st.caption("버튼을 누르면 AI가 이 단계를 과학적으로 분석합니다.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7. UI — 필터 바 (메인 상단)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def render_filters(df: pd.DataFrame) -> dict:
    """메인 화면 상단 expander에 독립 필터 위젯 배치. dict 반환."""
    with st.expander("🔍 필터 & 정렬", expanded=False):

        # Row 1: 시간 + 정렬
        r1c1, r1c2 = st.columns([3, 2])
        with r1c1:
            valid = df["_분"][df["_분"] < 9999]
            mx = int(valid.max()) if len(valid) else 120
            max_min = st.slider(
                "최대 소요 시간(분)", 0, max(mx, 120), max(mx, 120), step=5,
                help="0으로 놓으면 시간 필터 해제",
            )
        with r1c2:
            sort_by = st.selectbox("정렬", ["기본", "빠른 순", "만족도 순"])

        # Row 2: 재료 + 건강
        r2c1, r2c2 = st.columns(2)
        with r2c1:
            all_ing = _unique_values(df["핵심 식재료"])
            ingredient = st.selectbox(
                "핵심 식재료",
                [""] + all_ing,
                format_func=lambda x: x or "전체",
            )
        with r2c2:
            all_goals = _unique_values(df["건강"])
            health = st.selectbox(
                "건강 목적",
                [""] + all_goals,
                format_func=lambda x: x or "전체",
            )

        # Row 3: 분류
        all_cats = _unique_values(df["분류"])
        categories = st.multiselect("분류", all_cats)

    # 활성 필터 요약 칩
    chips = []
    if max_min and max_min < max(mx, 120):
        chips.append(f'<span class="filter-chip">⏱ {max_min}분 이내</span>')
    if ingredient:
        chips.append(f'<span class="filter-chip">🥩 {ingredient}</span>')
    if health:
        chips.append(f'<span class="filter-chip">💊 {health}</span>')
    for c in categories:
        chips.append(f'<span class="filter-chip">📂 {c}</span>')
    if chips:
        st.markdown(
            f'<div class="filter-summary">{"".join(chips)}</div>',
            unsafe_allow_html=True,
        )

    return {
        "max_minutes": max_min if max_min < max(mx, 120) else None,
        "ingredient": ingredient,
        "health": health,
        "categories": categories,
        "sort_by": sort_by,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 8. UI — 카드 리스트 (1열)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def render_card_list(filtered: pd.DataFrame, df_full: pd.DataFrame) -> None:
    """세로 1열 카드 리스트. 카드 클릭 → @st.dialog 모달."""
    total = len(filtered)

    if total == 0:
        st.markdown(
            '<div class="empty-state">'
            '<div class="icon">🍳</div>'
            '<p>조건에 맞는 메뉴가 없습니다.<br>필터를 조정해 보세요.</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f'<div class="result-bar">'
        f'<span class="result-count">{total}개 메뉴</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    rows = filtered.reset_index(drop=True)
    for idx in range(len(rows)):
        row = rows.iloc[idx]
        name = row["메뉴명"]

        # 태그 HTML
        tags = []
        time_v = str(row.get("소요 시간", ""))
        if time_v and time_v != "nan":
            tags.append(f'<span class="tag tag-time">{time_v}</span>')
        cat_v = str(row.get("분류", ""))
        if cat_v and cat_v != "nan":
            tags.append(f'<span class="tag tag-cat">{cat_v}</span>')
        health_v = str(row.get("건강", ""))
        if health_v and health_v != "nan":
            short = health_v[:18] + ("…" if len(health_v) > 18 else "")
            tags.append(f'<span class="tag tag-health">{short}</span>')
        sat_v = str(row.get("만족도", ""))
        if sat_v and sat_v != "nan":
            tags.append(f'<span class="tag tag-sat">★ {sat_v}</span>')

        ing_v = str(row.get("핵심 식재료", ""))
        ing_display = ""
        if ing_v and ing_v != "nan":
            ing_display = ing_v[:55] + ("…" if len(ing_v) > 55 else "")

        # 카드 HTML + 바로 아래 버튼
        st.markdown(
            f'<div class="m-card">'
            f'  <div class="m-card-title">{name}</div>'
            f'  <div class="m-card-tags">{"".join(tags)}</div>'
            f'  <div class="m-card-ing">{ing_display}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        if st.button(f"📋 레시피 보기", key=f"open_{idx}", use_container_width=True):
            show_detail(name, df_full)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 9. UI — 설정 (API 키 입력)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _render_settings():
    """API 키 입력 UI. secrets에 이미 있으면 '연결됨' 표시."""
    key_from_secrets, provider_from_secrets = "", ""
    try:
        key_from_secrets = st.secrets.get("LLM_API_KEY", "")
        provider_from_secrets = st.secrets.get("LLM_PROVIDER", "")
    except Exception:
        pass

    has_secrets_key = bool(key_from_secrets)
    current_key, current_provider = _get_llm_config()
    is_connected = bool(current_key)

    status = "🟢 연결됨" if is_connected else "⚫ 미연결"

    with st.expander(f"⚙️ AI 분석 설정 — {status}", expanded=False):
        if has_secrets_key:
            st.success("✅ secrets에서 API 키가 로드되었습니다.")
            st.caption(f"Provider: **{provider_from_secrets or 'openai'}** · 키: `{key_from_secrets[:8]}…`")
        else:
            st.caption("조리 단계별 과학적 분석을 사용하려면 API 키를 입력하세요.")
            c1, c2 = st.columns([2, 3])
            with c1:
                provider = st.selectbox(
                    "Provider",
                    ["openai", "gemini"],
                    index=0,
                    key="settings_provider",
                )
            with c2:
                api_key = st.text_input(
                    "API Key",
                    type="password",
                    placeholder="sk-… 또는 AI…",
                    key="settings_api_key",
                )

            # session_state에 저장
            if api_key:
                st.session_state["llm_api_key"] = api_key
                st.session_state["llm_provider"] = provider
                st.success(f"✅ {provider} 키 적용됨 (이 세션 동안 유지)")
            else:
                st.session_state["llm_api_key"] = ""

            st.caption(
                "💡 영구 저장하려면 `.streamlit/secrets.toml`에 "
                "`LLM_API_KEY`와 `LLM_PROVIDER`를 설정하세요."
            )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 10. 메인
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def main():
    st.set_page_config(
        page_title="Gourmet-OS",
        page_icon="🧬",
        layout="centered",       # ← 모바일 최적: centered
        initial_sidebar_state="collapsed",
    )
    st.markdown(MOBILE_CSS, unsafe_allow_html=True)

    # 헤더
    st.markdown(
        '<div class="app-header">'
        '<h1>Gourmet-OS</h1>'
        '<p>미식 대사 관리 관제탑</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── 설정 (API 키) ──
    _render_settings()

    # ── CSV URL 확보 ──
    csv_url = SHEET_CSV_URL
    if not csv_url:
        csv_url = st.text_input(
            "구글 시트 CSV URL",
            placeholder="https://docs.google.com/spreadsheets/d/e/…/pub?output=csv",
        )
        if not csv_url:
            st.markdown(
                '<div class="empty-state">'
                '<div class="icon">📋</div>'
                '<p>CSV URL을 입력하세요.</p>'
                '</div>',
                unsafe_allow_html=True,
            )
            st.stop()

    # ── 데이터 로드 ──
    with st.spinner("불러오는 중…"):
        df_full = load_data(csv_url)

    # ── 필터 (메인 상단) ──
    fparams = render_filters(df_full)

    # ── 필터링 (AND 결합) ──
    filtered = apply_filters(
        df_full,
        max_minutes=fparams["max_minutes"],
        ingredient=fparams["ingredient"],
        health_goal=fparams["health"],
        categories=fparams["categories"],
        sort_by=fparams["sort_by"],
    )

    # ── 카드 리스트 (1열) ──
    render_card_list(filtered, df_full)


if __name__ == "__main__":
    main()
