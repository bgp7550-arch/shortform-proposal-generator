import streamlit as st
import time
from scraper import scrape_landing_page
from ai_analyzer import create_client, analyze_product, generate_proposal


st.set_page_config(
    page_title="숏폼 광고 제안서 생성기",
    page_icon="🎬",
    layout="wide",
)

# --- 커스텀 CSS ---
st.markdown("""
<style>
    .main-title {
        text-align: center;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        text-align: center;
        color: #666;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    .stButton > button {
        width: 100%;
        background-color: #FF4B4B;
        color: white;
        font-size: 1.1rem;
        font-weight: 600;
        padding: 0.7rem;
        border: none;
        border-radius: 8px;
    }
    .stButton > button:hover {
        background-color: #FF3333;
        color: white;
    }
    div[data-testid="stStatusWidget"] {
        font-size: 0.95rem;
    }
</style>
""", unsafe_allow_html=True)

# --- API 키 로드 (Secrets 우선, 없으면 수동 입력) ---
api_key = st.secrets.get("ANTHROPIC_API_KEY", "")

with st.sidebar:
    st.header("설정")
    if api_key:
        st.success("API Key 설정됨 (Secrets)")
    else:
        api_key = st.text_input(
            "Claude API Key",
            type="password",
            placeholder="sk-ant-...",
            help="Anthropic에서 발급받은 API 키를 입력하세요.",
        )
    st.divider()
    st.markdown("### 사용 안내")
    st.markdown("""
1. 발신자명을 입력하세요
2. 자사몰 랜딩페이지 URL을 붙여넣으세요
3. **제안서 생성하기** 버튼을 클릭하세요
4. 분석 완료 후 제안서를 복사해 사용하세요
    """)
    st.divider()
    st.caption("Powered by Claude API")

# --- 메인 UI ---
st.markdown('<p class="main-title">🎬 숏폼 광고 제안서 생성기</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-title">랜딩페이지 URL을 붙여넣으면 소구점 분석 · 영상 기획안 · 제안서를 자동으로 만들어 드립니다.</p>',
    unsafe_allow_html=True,
)

st.divider()

col1, col2 = st.columns([1, 1])
with col1:
    sender_name = st.text_input(
        "✍️ 발신자명",
        placeholder="예: 홍길동",
        help="제안 이메일 하단에 들어갈 발신자 이름",
    )
with col2:
    url = st.text_input(
        "🔗 랜딩페이지 URL",
        placeholder="https://example.com/product",
        help="분석할 자사몰 상품 페이지 URL을 입력하세요",
    )

generate = st.button("🚀 제안서 생성하기", use_container_width=True)

# --- 생성 로직 ---
if generate:
    if not api_key:
        st.error("사이드바에서 Claude API Key를 입력해주세요.")
        st.stop()
    if not url:
        st.error("랜딩페이지 URL을 입력해주세요.")
        st.stop()
    if not sender_name:
        st.error("발신자명을 입력해주세요.")
        st.stop()

    client = create_client(api_key)

    # 1단계: 크롤링
    with st.status("랜딩페이지 내용을 수집하고 있습니다...", expanded=True) as status:
        st.write("📄 랜딩페이지 내용을 수집하고 있습니다...")
        try:
            page_data = scrape_landing_page(url)
        except Exception as e:
            st.error(f"크롤링 실패: {e}")
            st.stop()

        st.write(f"✅ 랜딩페이지 수집 완료 — **{page_data['title']}**")
        status.update(label="랜딩페이지 수집 완료 ✅", state="complete")

    # 2단계: 제품 분석
    with st.status("소구점을 분석하고 있습니다...", expanded=True) as status:
        st.write("🔍 고객 페르소나를 분석하고 있습니다...")
        time.sleep(0.5)
        st.write("🎯 소구점을 분석하고 있습니다...")

        analysis_placeholder = st.empty()
        analysis_text = ""
        try:
            for chunk in analyze_product(client, page_data):
                analysis_text += chunk
                analysis_placeholder.markdown(analysis_text)
        except Exception as e:
            st.error(f"분석 실패: {e}")
            st.stop()

        st.write("✅ 소구점 분석 완료")
        status.update(label="소구점 분석 완료 ✅", state="complete")

    # 3단계: 제안서 생성
    with st.status("제안서를 작성하고 있습니다...", expanded=True) as status:
        st.write("📝 제안서를 작성하고 있습니다...")

        proposal_placeholder = st.empty()
        proposal_text = ""
        try:
            for chunk in generate_proposal(client, analysis_text, sender_name):
                proposal_text += chunk
                proposal_placeholder.markdown(proposal_text)
        except Exception as e:
            st.error(f"제안서 생성 실패: {e}")
            st.stop()

        st.write("✅ 제안서 작성 완료")
        status.update(label="제안서 작성 완료 ✅", state="complete")

    # --- 결과 영역 ---
    st.divider()
    st.subheader("📋 최종 제안서")

    st.markdown(proposal_text)

    st.divider()

    # 복사용 텍스트
    st.text_area(
        "복사용 텍스트 (전체 선택 후 복사하세요)",
        value=proposal_text,
        height=300,
    )

    # 분석 결과도 펼쳐볼 수 있도록
    with st.expander("🔍 전체 분석 결과 보기"):
        st.markdown(analysis_text)
