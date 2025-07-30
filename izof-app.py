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
# session_state에 필요한 키들이 없으면 초기화합니다.
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
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
        match = re.match(r'^\s*(\S+)\s+(\d+)\s+(\d+)\s*$', line.strip())
        if match:
            item, required, current = match.groups()
            data.append({
                'item': item,
                'required': int(required),
                'current': int(current)
            })
    return data

def generate_analysis_prompt(parsed_data):
    """
    Gemini API에 전달할 프롬프트를 생성합니다. (개선된 버전)
    """
    data_str = "\n".join([f"- {d['item']}: 필요 점수 {d['required']}, 현재 점수 {d['current']}" for d in parsed_data])
    
    prompt = f"""
너는 세계 최고의 스포츠 심리학자이자 IZOF(개인별 최적 수행 상태 영역) 이론 전문가야. 너의 임무는 선수의 데이터를 분석하고 심층적인 맞춤형 보고서를 작성하는 것이다.

### IZOF 이론 핵심:
- '필요 점수'는 해당 선수가 최고의 기량을 발휘하기 위해 필요한 최적의 심리 상태 수준이다.
- '현재 점수'는 선수의 현재 심리 상태 수준이다.
- '필요 점수'와 '현재 점수'가 비슷할수록 최적의 상태(In the Zone)에 가까운 것이고, 차이가 클수록 불안정하거나 제 기량을 발휘하기 어려운 상태다.

### 새로운 지침: 데이터의 맥락 파악 및 심층 분석
- 아래 '분석 데이터'의 항목들을 보고, 이것이 일반적인 멘탈 검사인지, 아니면 특정 스포츠(예: 골프, 양궁, 축구, e스포츠 등)에 관련된 검사인지 먼저 파악하라.
- 만약 특정 스포츠가 연상된다면, 반드시 해당 스포츠의 특성을 고려하여 분석의 깊이를 더하라. 예를 들어, '드라이버 정확성'이라는 항목이 있다면 골프 선수에 초점을 맞춰 분석해야 한다.
- 모든 데이터 항목을 종합적으로 고려하되, 가장 중요하고 의미 있는 점들을 선별하여 보고서를 작성하라.

### 분석 데이터:
{data_str}

### 보고서 작성 지침 (아래 형식을 반드시 지켜라):
1.  **[종합 평가 및 맥락 파악]**: 데이터 전반을 기반으로 선수의 현재 멘탈 상태에 대한 총평과 함께, 이 데이터가 어떤 종류의 검사(일반 멘탈, 특정 스포츠 등)로 보이는지 먼저 언급하라.
2.  **[핵심 강점 분석]**: '현재 점수'가 '필요 점수'에 근접하거나 긍정적인 차이를 보이는 항목들 중에서 **가장 중요하고 의미 있는 강점 2~3가지를 짚어서** 설명하라.
3.  **[핵심 보완점 분석]**: '현재 점수'가 '필요 점수'보다 현저히 낮거나 높은 항목들 중에서 **가장 시급하거나 개선이 필요한 보완점 2~3가지를 짚어서** 설명하라. 점수가 낮은 것뿐만 아니라, 과도하게 높은 것도 문제가 될 수 있다는 점을 반드시 언급해야 한다. (예: 피로도가 필요 이상으로 높음)
4.  **[맞춤형 훈련 제안]**: 위에서 분석한 보완점을 개선하기 위해, 파악된 스포츠나 상황에 맞는 구체적인 멘탈 훈련법 2가지를 제안하라.
"""
    return prompt

def create_bar_chart(df):
    """
    분석 데이터를 바탕으로 비교 막대 그래프를 생성합니다.
    """
    df_melted = pd.melt(df, id_vars=['item'], value_vars=['required', 'current'],
                        var_name='score_type', value_name='score')
    df_melted['score_type'] = df_melted['score_type'].map({'required': '필요 점수', 'current': '현재 점수'})

    fig = px.bar(df_melted, 
                 x='item', 
                 y='score', 
                 color='score_type',
                 barmode='group',
                 title='<b>필요 점수 vs 현재 점수 비교</b>',
                 labels={'item': '<b>평가 항목</b>', 'score': '<b>점수</b>', 'score_type': '<b>점수 유형</b>'},
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

# --- 사이드바: API 키 입력 및 설명 ---
with st.sidebar:
    st.header("설정")
    api_key = st.text_input("Google Gemini API 키를 입력하세요.", type="password", help="API 키는 [Google AI Studio](https://aistudio.google.com/app/apikey)에서 발급받을 수 있습니다.")
    st.divider()
    st.header("사용 방법")
    st.markdown("""
    1.  **API 키**를 입력하세요.
    2.  **'검사 결과 입력'** 칸에 자신의 IZOF 검사 결과를 붙여넣으세요.
    3.  **'분석하기'** 버튼을 클릭하여 AI의 텍스트 분석을 확인하세요.
    4.  **'상세 리포트 보기'** 버튼을 눌러 점수 비교 그래프를 확인하세요.
    """)

# --- 메인 화면: 데이터 입력 및 결과 출력 (세로 정렬) ---
st.subheader("1. 검사 결과 입력")
placeholder_text = """# 아래 형식에 맞춰 데이터를 입력하세요.
# (항목 필요점수 현재점수)
# 예시 (골프):
드라이버정확도 8 6
퍼팅자신감 9 7
코스매니지먼트 8 8
긴장조절 7 5
승부욕 8 9
"""
user_input = st.text_area(
    "IZOF 검사 결과를 여기에 붙여넣으세요.", 
    height=250, 
    placeholder=placeholder_text
)

# "분석하기" 버튼
if st.button("🚀 분석하기", type="primary", use_container_width=True):
    if not api_key:
        st.error("❗️ 사이드바에 Gemini API 키를 먼저 입력해주세요.")
    elif not user_input:
        st.error("❗️ 분석할 데이터를 입력해주세요.")
    else:
        # 이전 결과 초기화
        st.session_state.analysis_result = None
        st.session_state.chart_data = None
        st.session_state.show_report = False
        
        with st.spinner("AI가 당신의 멘탈 상태를 분석 중입니다..."):
            try:
                # 1. 데이터 파싱
                parsed_data = parse_data(user_input)
                if not parsed_data:
                    st.error("❗️ 입력 데이터 형식을 확인해주세요. '항목 점수 점수' 형식으로 각 줄에 입력해야 합니다.")
                else:
                    # 2. Gemini API 호출
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = generate_analysis_prompt(parsed_data)
                    response = model.generate_content(prompt)
                    
                    # 3. 결과 저장 (세션 상태 활용)
                    st.session_state.analysis_result = response.text
                    st.session_state.chart_data = pd.DataFrame(parsed_data)

            except Exception as e:
                st.error(f"⚠️ 분석 중 오류가 발생했습니다: {e}")

# --- 결과 출력 영역 ---
if st.session_state.analysis_result:
    st.divider()
    st.subheader("2. AI 분석 결과")
    st.markdown(st.session_state.analysis_result)
    
    # "상세 리포트 보기" 버튼
    if st.button("📊 상세 리포트 보기", use_container_width=True):
        st.session_state.show_report = not st.session_state.show_report # 토글 기능

# 상세 리포트 (그래프) 출력
if st.session_state.show_report and st.session_state.chart_data is not None:
    st.subheader("3. 상세 리포트: 점수 비교 그래프")
    fig = create_bar_chart(st.session_state.chart_data)
    st.plotly_chart(fig, use_container_width=True)
