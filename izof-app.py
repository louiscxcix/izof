import streamlit as st
import google.generativeai as genai
import plotly.express as px
import pandas as pd
import re

# --- 페이지 기본 설정 ---
st.set_page_config(
    page_title="IZOF 멘탈 분석기",
    page_icon="🧠",
    layout="wide",
)

# --- 상태 초기화 ---
if 'summary_report' not in st.session_state:
    st.session_state.summary_report = None
if 'detailed_report' not in st.session_state:
    st.session_state.detailed_report = None
if 'chart_data' not in st.session_state:
    st.session_state.chart_data = None
if 'show_report' not in st.session_state:
    st.session_state.show_report = False


# --- 핵심 기능 함수 ---

def parse_data(text_data):
    """
    사용자가 입력한 텍스트 데이터를 파싱하여
    항목, 필요 점수, 현재 점수로 분리합니다.
    """
    lines = text_data.strip().split('\n')
    data = []
    for line in lines:
        if line.strip().startswith('#') or not line.strip():
            continue
        # [수정된 부분] 항목 이름에 띄어쓰기가 있어도 인식하도록 정규표현식 변경
        match = re.match(r'^\s*(.+?)\s+(\d+)\s+(\d+)\s*$', line.strip())
        if match:
            item, required, current = match.groups()
            data.append({
                '항목': item.strip(), # 항목 앞뒤 공백 제거
                '필요 점수': int(required),
                '현재 점수': int(current)
            })
    return data

def generate_analysis_prompt(parsed_data):
    """
    Gemini API에 전달할 프롬프트를 생성합니다. (요약/상세 분리)
    """
    data_str = "\n".join([f"- {d['항목']}: 필요 점수 {d['필요 점수']}, 현재 점수 {d['현재 점수']}" for d in parsed_data])
    
    prompt = f"""
너는 세계 최고의 스포츠 심리학자이자 IZOF(개인별 최적 수행 상태 영역) 이론 전문가야. 너의 임무는 선수의 데이터를 분석하고, [요약 보고서]와 [상세 보고서] 두 부분으로 나누어 심층적인 맞춤형 보고서를 작성하는 것이다.

### IZOF 이론 핵심:
- '필요 점수'는 해당 선수가 최고의 기량을 발휘하기 위해 필요한 최적의 심리 상태 수준이다.
- '현재 점수'는 선수의 현재 심리 상태 수준이다.

### 보고서 작성 지침 (아래 두 파트의 형식을 반드시 지켜서 응답하라):

---
### [요약 보고서]
- **핵심 강점:** 현재 가장 돋보이는 강점 1~2개를 키워드 형태로 간결하게 작성하라.
- **핵심 보완점:** 개선이 가장 시급한 보완점 1~2개를 키워드 형태로 간결하게 작성하라.
---
### [상세 보고서]
1.  **[종합 평가 및 맥락 파악]**: 데이터 전반을 기반으로 선수의 현재 멘탈 상태에 대한 총평과 함께, 이 데이터가 어떤 종류의 검사(일반 멘탈, 특정 스포츠 등)로 보이는지 먼저 언급하라.
2.  **[핵심 강점 분석]**: '현재 점수'가 '필요 점수'에 근접하거나 긍정적인 차이를 보이는 항목들 중에서 **가장 중요하고 의미 있는 강점 2~3가지를 짚어서** 상세히 설명하라.
3.  **[핵심 보완점 분석]**: '현재 점수'가 '필요 점수'보다 현저히 낮거나 높은 항목들 중에서 **가장 시급하거나 개선이 필요한 보완점 2~3가지를 짚어서** 상세히 설명하라. 점수가 낮은 것뿐만 아니라, 과도하게 높은 것도 문제가 될 수 있다는 점을 반드시 언급해야 한다.
4.  **[맞춤형 훈련 제안]**: 위에서 분석한 보완점을 개선하기 위해, 파악된 스포츠나 상황에 맞는 구체적인 멘탈 훈련법 2가지를 제안하라.
"""
    return prompt

def create_bar_chart(df):
    """
    분석 데이터를 바탕으로 비교 막대 그래프를 생성합니다.
    """
    df_melted = pd.melt(df, id_vars=['항목'], value_vars=['필요 점수', '현재 점수'],
                        var_name='점수 유형', value_name='점수')

    fig = px.bar(df_melted, 
                 x='항목', 
                 y='점수', 
                 color='점수 유형',
                 barmode='group',
                 title='<b>필요 점수 vs 현재 점수 비교</b>',
                 labels={'항목': '<b>평가 항목</b>', '점수': '<b>점수</b>', '점수 유형': '<b>점수 유형</b>'},
                 text_auto=True,
                 color_discrete_map={'필요 점수': '#636EFA', '현재 점수': '#FFA15A'})
    
    fig.update_layout(
        font=dict(family="Arial, sans-serif", size=12),
        legend_title_text='',
        yaxis=dict(range=[0, 11])
    )
    fig.update_traces(textposition='outside')
    return fig

# --- Streamlit UI 구성 ---

st.title("🧠 IZOF 멘탈 분석기 with Gemini")
st.markdown("> IZOF(Individual Zones of Optimal Functioning) 이론을 바탕으로 당신의 멘탈 상태를 분석하고 맞춤형 훈련법을 제안합니다.")
st.divider()

# --- 사이드바 ---
with st.sidebar:
    # [수정된 부분] st.expander를 사용해 기본적으로 접혀있도록 변경
    with st.expander("사용 방법 보기"):
        st.markdown("""
        1.  **'검사 결과 입력'** 칸에 자신의 IZOF 검사 결과를 붙여넣으세요.
        2.  **'분석하기'** 버튼을 클릭하여 AI의 텍스트 분석을 확인하세요.
        3.  **'상세 리포트 보기'** 버튼을 눌러 점수 비교 그래프를 확인하세요.
        """)

# --- 메인 화면 ---
st.subheader("1. 검사 결과 입력")
placeholder_text = """# 아래 형식에 맞춰 데이터를 입력하세요.
# (항목 필요점수 현재점수)
# 예시 (골프):
드라이버 정확도 8 6
퍼팅 자신감 9 7
코스 매니지먼트 8 8
긴장 조절 7 5
승부욕 8 9
"""
user_input = st.text_area(
    "IZOF 검사 결과를 여기에 붙여넣으세요.", 
    height=250, 
    placeholder=placeholder_text
)

# "분석하기" 버튼
if st.button("🚀 분석하기", type="primary", use_container_width=True):
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("오류: 앱 관리자가 API 키를 설정하지 않았습니다.")
        st.stop()
    
    if not user_input:
        st.error("❗️ 분석할 데이터를 입력해주세요.")
    else:
        st.session_state.summary_report = None
        st.session_state.detailed_report = None
        st.session_state.chart_data = None
        st.session_state.show_report = False
        
        with st.spinner("AI가 당신의 멘탈 상태를 분석 중입니다..."):
            try:
                parsed_data = parse_data(user_input)
                if not parsed_data:
                    st.error("❗️ 입력 데이터 형식을 확인해주세요. '항목 점수 점수' 형식으로 각 줄에 입력해야 합니다.")
                else:
                    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = generate_analysis_prompt(parsed_data)
                    response = model.generate_content(prompt)
                    
                    # [수정된 부분] 응답을 요약과 상세로 분리
                    response_text = response.text
                    if "### [상세 보고서]" in response_text:
                        parts = response_text.split("### [상세 보고서]")
                        summary = parts[0].replace("### [요약 보고서]", "").strip()
                        detailed = "### [상세 보고서]\n" + parts[1].strip()
                    else: # 분리 실패 시 예외 처리
                        summary = "요약 보고서를 생성하지 못했습니다. 전체 결과를 확인하세요."
                        detailed = response_text

                    st.session_state.summary_report = summary
                    st.session_state.detailed_report = detailed
                    st.session_state.chart_data = pd.DataFrame(parsed_data)

            except Exception as e:
                st.error(f"⚠️ 분석 중 오류가 발생했습니다: {e}")

# --- 결과 출력 영역 ---
# [수정된 부분] 요약 보고서 먼저 출력
if st.session_state.summary_report:
    st.divider()
    st.subheader("2. AI 요약 분석")
    
    # 입력 데이터 테이블 표시
    if st.session_state.chart_data is not None:
        st.dataframe(st.session_state.chart_data, use_container_width=True)

    st.markdown(st.session_state.summary_report)
    
    if st.button("📊 상세 리포트 보기", use_container_width=True):
        st.session_state.show_report = not st.session_state.show_report

# [수정된 부분] 버튼 클릭 시 상세 리포트 출력
if st.session_state.show_report and st.session_state.detailed_report:
    st.subheader("3. 상세 리포트") # 제목 변경
    st.markdown(st.session_state.detailed_report) # 상세 분석 내용 추가
    fig = create_bar_chart(st.session_state.chart_data)
    st.plotly_chart(fig, use_container_width=True)