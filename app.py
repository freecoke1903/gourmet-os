"""
Gourmet-OS v4
━━━━━━━━━━━━━
결정 모드(냉장고 매칭) + AI 요리도우미 중심 재설계
"""

import re
import textwrap

import pandas as pd
import streamlit as st

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 0. 설정
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _secret(key: str, fallback: str = "") -> str:
    try:
        return st.secrets[key]
    except Exception:
        return fallback


SHEET_CSV_URL: str = _secret("SHEET_CSV_URL", "")
REQUIRED_COLUMNS = [
    "메뉴명", "만족도", "분류", "건강",
    "소요 시간", "핵심 식재료", "부재료/소스", "조리법 (통합)",
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. CSS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
:root {
    --bg:#f7f6f3; --surface:#fff; --border:#e5e2db;
    --text1:#1a1a1a; --text2:#666; --text3:#999;
    --accent:#2d2d2d;
    --t-time-bg:#f0efe9; --t-time:#555;
    --t-cat-bg:#e8f4e8; --t-cat:#2d6a2d;
    --t-hp-bg:#e8eef8; --t-hp:#2d4a8a;
    --t-sat-bg:#fff8e8; --t-sat:#8a6a2d;
    --t-match-bg:#e2f5e9; --t-match:#1a7a3a;
}
.stApp{font-family:'Noto Sans KR',sans-serif;background:var(--bg)}
.block-container{max-width:640px!important;padding:1rem 1rem 4rem!important}
section[data-testid="stSidebar"],
button[data-testid="stSidebarCollapsedControl"]{display:none!important}

/* 헤더 */
.hd{text-align:center;padding:.6rem 0 .4rem;border-bottom:2px solid var(--accent);margin-bottom:.8rem}
.hd h1{font-size:1.25rem;font-weight:700;color:var(--text1);margin:0}
.hd p{font-size:.72rem;color:var(--text3);margin:.1rem 0 0;font-weight:300}

/* 냉장고 입력 */
.fridge-label{font-size:.88rem;font-weight:600;color:var(--text1);margin-bottom:.3rem}
.fridge-hint{font-size:.73rem;color:var(--text3);margin-top:.15rem}

/* 필터 칩 */
.chips{display:flex;flex-wrap:wrap;gap:.3rem;margin:.4rem 0 .6rem}
.chip{display:inline-block;font-size:.68rem;padding:.12rem .5rem;border-radius:20px;white-space:nowrap}
.chip-ing{background:var(--t-match-bg);color:var(--t-match)}
.chip-time{background:var(--t-time-bg);color:var(--t-time)}
.chip-cat{background:var(--t-cat-bg);color:var(--t-cat)}
.chip-hp{background:var(--t-hp-bg);color:var(--t-hp)}

/* 카드 */
.mc{background:var(--surface);border:1px solid var(--border);border-radius:10px;
    padding:.85rem 1rem;margin-bottom:.5rem;transition:border-color .12s}
.mc:active{border-color:var(--accent)}
.mc-name{font-size:.95rem;font-weight:600;color:var(--text1);margin-bottom:.35rem;line-height:1.35}
.mc-tags{display:flex;flex-wrap:wrap;gap:.3rem;margin-bottom:.3rem}
.tag{display:inline-block;font-size:.67rem;padding:.1rem .48rem;border-radius:20px;white-space:nowrap}
.tag-time{background:var(--t-time-bg);color:var(--t-time)}
.tag-cat{background:var(--t-cat-bg);color:var(--t-cat)}
.tag-hp{background:var(--t-hp-bg);color:var(--t-hp)}
.tag-sat{background:var(--t-sat-bg);color:var(--t-sat)}
.tag-match{background:var(--t-match-bg);color:var(--t-match);font-weight:500}
.mc-ing{font-size:.74rem;color:var(--text3);line-height:1.5}

/* 카운트 */
.cnt{font-size:.8rem;color:var(--text2);margin-bottom:.5rem}

/* 빈 상태 */
.empty{text-align:center;padding:2.5rem 1rem;color:var(--text3)}
.empty .ico{font-size:2.2rem;margin-bottom:.4rem}
.empty p{font-size:.88rem}

/* 모달 내부 */
.d-tags{display:flex;flex-wrap:wrap;gap:.35rem;margin:.5rem 0}
.d-div{height:1px;background:var(--border);margin:.7rem 0}
.d-sec{font-size:.82rem;font-weight:600;color:var(--text2);margin-bottom:.3rem}
.d-list{list-style:none;padding:0;margin:0}
.d-list li{font-size:.82rem;color:var(--text2);padding:.08rem 0}
.d-list li::before{content:"· ";color:var(--text3)}

/* 카드 내 아이콘 버튼 */
.mc + div button {
    background: transparent !important; border: 1px solid var(--border) !important;
    border-radius: 8px !important; width: 36px !important; min-width: 36px !important;
    height: 32px !important; padding: 0 !important; margin: -0.6rem 0 0.5rem auto !important;
    display: block !important; font-size: .9rem !important;
    transition: border-color .12s !important;
}
.mc + div button:hover { border-color: var(--accent) !important; }

/* 설정 */
div[data-testid="stExpander"] details{border:1px solid var(--border)!important;border-radius:8px!important}
</style>
"""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. 데이터 로드
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@st.cache_data(ttl=3600, show_spinner=False)
def load_data(csv_url: str) -> pd.DataFrame:
    df = pd.read_csv(csv_url)
    df.columns = [c.strip() for c in df.columns]
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        st.error(f"CSV에 다음 컬럼이 없습니다: {missing}")
        st.stop()
    df["_분"] = df["소요 시간"].apply(_parse_min)
    df["_만족도"] = pd.to_numeric(df["만족도"], errors="coerce").fillna(0)
    # 식재료 정규화 컬럼 (검색용): 괄호/브랜드 제거
    df["_핵심재료_정규"] = df["핵심 식재료"].fillna("").apply(_normalize_ingredients)
    return df


def _parse_min(raw) -> int:
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


def _normalize_ingredient(name: str) -> str:
    """
    '버섯 (밀프랩)' → '버섯'
    '닭가슴살(냉동)' → '닭가슴살'
    괄호 안 내용 제거 후 기본 재료명만 추출.
    """
    return re.sub(r"\s*[\(\（][^)）]*[\)\）]", "", name).strip()


def _normalize_ingredients(raw: str) -> str:
    """쉼표로 분리된 재료 문자열 전체를 정규화."""
    parts = [_normalize_ingredient(p.strip()) for p in raw.split(",") if p.strip()]
    return ",".join(parts)


def _unique_ingredients(df: pd.DataFrame) -> list[str]:
    """정규화된 재료 고유 목록."""
    return sorted({
        v.strip()
        for raw in df["_핵심재료_정규"].dropna()
        for v in raw.split(",") if v.strip()
    })


def _unique_values(series: pd.Series, sep: str = ",") -> list[str]:
    return sorted({
        v.strip() for raw in series.dropna()
        for v in str(raw).split(sep) if v.strip()
    })


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. 필터링 엔진
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def apply_filters(
    df: pd.DataFrame,
    fridge: list[str],
    max_minutes: int | None,
    categories: list[str],
    health_goal: str,
    sort_by: str,
) -> pd.DataFrame:
    """모든 필터 AND 결합. fridge는 OR(재료 중 하나라도 매칭)."""
    out = df.copy()

    # ★ 냉장고 매칭: 정규화된 컬럼에서 contains 검색 (OR)
    if fridge:
        mask = pd.Series(False, index=out.index)
        for ing in fridge:
            ing = ing.strip()
            if ing:
                mask = mask | out["_핵심재료_정규"].str.contains(
                    ing, case=False, regex=False
                )
        out = out[mask]

    if max_minutes is not None:
        out = out[out["_분"] <= max_minutes]

    if categories:
        out = out[out["분류"].fillna("").apply(
            lambda x: any(c in str(x) for c in categories)
        )]

    if health_goal:
        out = out[out["건강"].fillna("").str.contains(
            health_goal.strip(), case=False, regex=False
        )]

    if sort_by == "빠른 순":
        out = out.sort_values("_분")
    elif sort_by == "만족도 순":
        out = out.sort_values("_만족도", ascending=False)

    return out


def count_matches(row_normalized: str, fridge: list[str]) -> int:
    """매칭된 재료 개수."""
    return sum(1 for ing in fridge if ing and ing.lower() in row_normalized.lower())


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. AI 가이드 (nice-to-have, 축소)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SYSTEM_PROMPT = textwrap.dedent("""\
    당신은 Gourmet-OS 분석 엔진입니다.
    조리 단계를 물리·화학·생리학적 관점에서 해설하는 전문 분석관.
    톤: 객관적, 과학적. 이모지 금지.
    깊이: 왜 그래야 하는지 이유(마이야르 반응, 캐러멜화, 전분 호화 등)를
    온도·시간 수치와 함께 3-5문장으로 설명.
    언어: 한국어(과학 용어 영문 병기).
    형식: [핵심 원리] → [최적 조건] → [실패 시나리오] → [팁]
""")


def _get_llm_key() -> tuple[str, str]:
    key = _secret("LLM_API_KEY") or st.session_state.get("llm_api_key", "")
    provider = _secret("LLM_PROVIDER", "openai") if _secret("LLM_API_KEY") \
        else st.session_state.get("llm_provider", "openai")
    return key, provider


@st.cache_data(ttl=86400, show_spinner=False)
def _llm_call(step: str, menu: str, provider: str, api_key: str) -> str:
    msg = f"메뉴: {menu}\n조리 단계를 해설하라.\n\n{step}"
    if provider == "openai":
        try:
            from openai import OpenAI
            r = OpenAI(api_key=api_key).chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": SYSTEM_PROMPT},
                          {"role": "user", "content": msg}],
                temperature=0.3, max_tokens=600)
            return r.choices[0].message.content
        except Exception as e:
            return f"⚠️ 호출 실패: {e}"
    if provider == "gemini":
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            m = genai.GenerativeModel("gemini-1.5-flash", system_instruction=SYSTEM_PROMPT)
            return m.generate_content(msg).text
        except Exception as e:
            return f"⚠️ 호출 실패: {e}"
    return ""


def get_analysis(step: str, menu: str) -> str:
    key, provider = _get_llm_key()
    if not key:
        return "API 키 미설정 — ⚙️ 설정에서 키를 입력하면 활성화됩니다."
    return _llm_call(step, menu, provider, key)


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
# 6. 레시피 상세 모달
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@st.dialog("📋 레시피", width="large")
def show_detail(menu_name: str, df_full: pd.DataFrame):
    """레시피 상세 — 원본 df에서 조회하여 필터 변경에 안전."""
    match = df_full[df_full["메뉴명"] == menu_name]
    if match.empty:
        st.error("메뉴를 찾을 수 없습니다.")
        return

    row = match.iloc[0]

    # 태그
    tags = []
    for val, cls in [("소요 시간", "tag-time"), ("분류", "tag-cat"), ("건강", "tag-hp")]:
        v = str(row.get(val, ""))
        if v and v != "nan":
            tags.append(f'<span class="tag {cls}">{v}</span>')
    sat = str(row.get("만족도", ""))
    if sat and sat != "nan":
        tags.append(f'<span class="tag tag-sat">★ {sat}</span>')
    if tags:
        st.markdown(f'<div class="d-tags">{"".join(tags)}</div>', unsafe_allow_html=True)

    # ── AI 요리도우미 (맨 위, 전체 단계 한 번에) ──
    steps = split_steps(str(row.get("조리법 (통합)", "")))
    if steps:
        with st.expander("🤖 AI 요리도우미 — 과학 기반 조리 가이드", expanded=False):
            key, _ = _get_llm_key()
            if not key:
                st.caption("⚙️ 하단 AI 설정에서 API 키를 입력하면 활성화됩니다.")
            else:
                cache_key = f"ai_result_{menu_name}"
                if cache_key in st.session_state:
                    st.markdown(st.session_state[cache_key])
                else:
                    if st.button("🔬 전체 단계 분석 실행", key=f"ai_all_{menu_name}",
                                 use_container_width=True):
                        all_steps_text = "\n".join(
                            f"[{i+1}단계] {s}" for i, s in enumerate(steps)
                        )
                        with st.spinner("전체 단계 분석 중…"):
                            result = get_analysis(all_steps_text, menu_name)
                        st.session_state[cache_key] = result
                        st.markdown(result)

    # ── 식재료 ──
    st.markdown('<div class="d-div"></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        core = [i.strip() for i in str(row.get("핵심 식재료", "")).split(",") if i.strip()]
        if core:
            items = "".join(f"<li>{i}</li>" for i in core)
            st.markdown(f'<div class="d-sec">핵심 식재료</div><ul class="d-list">{items}</ul>',
                        unsafe_allow_html=True)
    with c2:
        sub = [i.strip() for i in str(row.get("부재료/소스", "")).split(",") if i.strip()]
        if sub:
            items = "".join(f"<li>{i}</li>" for i in sub)
            st.markdown(f'<div class="d-sec">부재료 / 소스</div><ul class="d-list">{items}</ul>',
                        unsafe_allow_html=True)

    # ── 조리법 전문 ──
    st.markdown('<div class="d-div"></div>', unsafe_allow_html=True)
    st.markdown('<div class="d-sec">조리법</div>', unsafe_allow_html=True)
    if steps:
        for i, step in enumerate(steps, 1):
            st.markdown(f"**{i}.** {step}")
    else:
        st.info("조리법 데이터가 비어 있습니다.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 8. 메인 화면 UI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def render_fridge_input() -> list[str]:
    """냉장고 재료 입력 — 앱의 핵심 입력."""
    st.markdown('<div class="fridge-label">🧊 냉장고에 뭐 있어?</div>', unsafe_allow_html=True)
    raw = st.text_input(
        "재료 입력",
        placeholder="예: 버섯, 닭가슴살, 양파",
        label_visibility="collapsed",
    )
    st.markdown('<div class="fridge-hint">쉼표로 여러 재료 입력 · 입력 안 하면 전체 메뉴 표시</div>',
                unsafe_allow_html=True)
    if not raw.strip():
        return []
    return [i.strip() for i in raw.split(",") if i.strip()]


def render_sub_filters(df: pd.DataFrame) -> dict:
    """보조 필터 (접힌 상태)."""
    with st.expander("⚙️ 추가 필터 & 정렬", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            valid = df["_분"][df["_분"] < 9999]
            mx = int(valid.max()) if len(valid) else 120
            max_min = st.slider("최대 시간(분)", 0, max(mx, 120), max(mx, 120), step=5)
        with c2:
            sort_by = st.selectbox("정렬", ["기본", "빠른 순", "만족도 순"])

        c3, c4 = st.columns(2)
        with c3:
            cats = st.multiselect("분류", _unique_values(df["분류"]))
        with c4:
            goals = _unique_values(df["건강"])
            health = st.selectbox("건강", [""] + goals, format_func=lambda x: x or "전체")

    return {
        "max_minutes": max_min if max_min < max(mx, 120) else None,
        "categories": cats,
        "health": health,
        "sort_by": sort_by,
    }


def render_active_chips(fridge: list[str], filters: dict):
    """활성 필터를 칩으로 표시."""
    chips = []
    for ing in fridge:
        chips.append(f'<span class="chip chip-ing">🥩 {ing}</span>')
    if filters["max_minutes"]:
        chips.append(f'<span class="chip chip-time">⏱ {filters["max_minutes"]}분</span>')
    for c in filters["categories"]:
        chips.append(f'<span class="chip chip-cat">📂 {c}</span>')
    if filters["health"]:
        chips.append(f'<span class="chip chip-hp">💊 {filters["health"]}</span>')
    if chips:
        st.markdown(f'<div class="chips">{"".join(chips)}</div>', unsafe_allow_html=True)


def render_cards(filtered: pd.DataFrame, df_full: pd.DataFrame, fridge: list[str]):
    """1열 카드 리스트."""
    total = len(filtered)
    if total == 0:
        st.markdown(
            '<div class="empty"><div class="ico">🍳</div>'
            '<p>조건에 맞는 메뉴가 없습니다.<br>필터를 조정해 보세요.</p></div>',
            unsafe_allow_html=True)
        return

    st.markdown(f'<div class="cnt">{total}개 메뉴</div>', unsafe_allow_html=True)

    rows = filtered.reset_index(drop=True)
    for idx in range(len(rows)):
        row = rows.iloc[idx]
        name = row["메뉴명"]

        # 태그
        tags = ""
        # 매칭 재료 수 표시
        if fridge:
            n = count_matches(str(row.get("_핵심재료_정규", "")), fridge)
            if n:
                tags += f'<span class="tag tag-match">{n}개 재료 매칭</span>'
        tv = str(row.get("소요 시간", ""))
        if tv and tv != "nan":
            tags += f'<span class="tag tag-time">{tv}</span>'
        cv = str(row.get("분류", ""))
        if cv and cv != "nan":
            tags += f'<span class="tag tag-cat">{cv}</span>'
        hv = str(row.get("건강", ""))
        if hv and hv != "nan":
            short = hv[:18] + ("…" if len(hv) > 18 else "")
            tags += f'<span class="tag tag-hp">{short}</span>'
        sv = str(row.get("만족도", ""))
        if sv and sv != "nan":
            tags += f'<span class="tag tag-sat">★ {sv}</span>'

        # 재료 미리보기
        ing = str(row.get("핵심 식재료", ""))
        ing_disp = ""
        if ing and ing != "nan":
            ing_disp = ing[:55] + ("…" if len(ing) > 55 else "")

        st.markdown(
            f'<div class="mc">'
            f'<div class="mc-name">{name}</div>'
            f'<div class="mc-tags">{tags}</div>'
            f'<div class="mc-ing">{ing_disp}</div>'
            f'</div>',
            unsafe_allow_html=True)

        if st.button("📋", key=f"det_{idx}", help="레시피 보기"):
            show_detail(name, df_full)


def render_settings():
    """API 키 설정 (최하단, 축소)."""
    key, provider = _get_llm_key()
    status = "🟢" if key else "⚫"

    with st.expander(f"⚙️ AI 설정 {status}", expanded=False):
        if _secret("LLM_API_KEY"):
            st.success(f"secrets에서 로드됨 ({_secret('LLM_PROVIDER', 'openai')})")
        else:
            c1, c2 = st.columns([2, 3])
            with c1:
                prov = st.selectbox("Provider", ["openai", "gemini"], key="s_prov")
            with c2:
                k = st.text_input("API Key", type="password", key="s_key")
            if k:
                st.session_state["llm_api_key"] = k
                st.session_state["llm_provider"] = prov
                st.success(f"✅ {prov} 키 적용됨")
            st.caption("영구 저장: Streamlit Cloud Settings → Secrets")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 9. 메인
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def main():
    st.set_page_config(
        page_title="Gourmet-OS", page_icon="🧬",
        layout="centered", initial_sidebar_state="collapsed",
    )
    st.markdown(CSS, unsafe_allow_html=True)

    # 헤더
    st.markdown(
        '<div class="hd"><h1>Gourmet-OS</h1><p>냉장고 → 메뉴 결정 → 조리</p></div>',
        unsafe_allow_html=True)

    # CSV
    csv_url = SHEET_CSV_URL
    if not csv_url:
        csv_url = st.text_input("CSV URL", placeholder="구글 시트 CSV 배포 URL")
        if not csv_url:
            st.markdown('<div class="empty"><div class="ico">📋</div><p>CSV URL을 입력하세요.</p></div>',
                        unsafe_allow_html=True)
            st.stop()

    with st.spinner("불러오는 중…"):
        df_full = load_data(csv_url)

    # ── 핵심 입력: 냉장고 재료 ──
    fridge = render_fridge_input()

    # ── 보조 필터 ──
    filters = render_sub_filters(df_full)

    # ── 활성 필터 칩 ──
    render_active_chips(fridge, filters)

    # ── 필터링 ──
    filtered = apply_filters(
        df_full,
        fridge=fridge,
        max_minutes=filters["max_minutes"],
        categories=filters["categories"],
        health_goal=filters["health"],
        sort_by=filters["sort_by"],
    )

    # 냉장고 매칭 시 매칭 수 기준 정렬 (기본 정렬일 때)
    if fridge and filters["sort_by"] == "기본":
        filtered = filtered.copy()
        filtered["_매칭수"] = filtered["_핵심재료_정규"].apply(
            lambda x: count_matches(x, fridge)
        )
        filtered = filtered.sort_values("_매칭수", ascending=False)

    # ── 카드 리스트 ──
    render_cards(filtered, df_full, fridge)

    # ── 설정 (최하단) ──
    st.markdown("---")
    render_settings()


if __name__ == "__main__":
    main()
