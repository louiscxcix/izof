import os
import re
from datetime import datetime

import google.generativeai as genai
import pandas as pd
import plotly.express as px
import pytz
import streamlit as st

# --- 페이지 기본 설정 ---
st.set_page_config(
    page_title="IZOF 멘탈 분석기",
    page_icon="🧠",
    layout="wide",
)

# --- 상태 초기화 ---
if "summary_report" not in st.session_state:
    st.session_state.summary_report = None
if "detailed_report" not in st.session_state:
    st.session_state.detailed_report = None
if "chart_data" not in st.session_state:
    st.session_state.chart_data = None
if "show_report" not in st.session_state:
    st.session_state.show_report = False
if "analysis_date" not in st.session_state:
    st.session_state.analysis_date = None


# --- 핵심 기능 함수 ---


def parse_data(text_data):
    """
    사용자가 입력한 텍스트 데이터를 파싱하여
    항목, 필요 점수, 현재 점수로 분리합니다.
    """
    lines = text_data.strip().split("\n")
    data = []
    for line in lines:
        if line.strip().startswith("#") or not line.strip():
            continue
        match = re.match(r"^\s*(.+?)\s+(\d+)\s+(\d+)\s*$", line.strip())
        if match:
            item, required, current = match.groups()
            data.append(
                {
                    "항목": item.strip(),
                    "필요 점수": int(required),
                    "현재 점수": int(current),
                }
            )
    return data


def generate_analysis_prompt(parsed_data):
    """
    [개선된 버전] Gemini API에 전달할 프롬프트를 생성합니다.
    """
    data_str = "\n".join(
        [
            f"- {d['항목']}: 필요 점수 {d['필요 점수']}, 현재 점수 {d['현재 점수']}"
            for d in parsed_data
        ]
    )

    prompt = f"""
너는 개인별 최적수행상태(IZOF) 이론에 기반한 수행 프로파일링 전문가다. 너의 임무는 선수의 심리, 기술, 체력 데이터를 종합적으로 분석하고, 그 결과를 바탕으로 전문가 수준의 보고서를 [요약 보고서]와 [상세 보고서] 두 부분으로 나누어 작성하는 것이다.

### 너가 학습해야 할 IZOF 이론의 핵심 원리:
- **개인 맞춤형 분석:** 모든 선수는 자신만의 최적 수행 상태(Zone)가 다르다. 분석은 이 개인차를 반드시 고려해야 한다.
- **'요구 점수'와 '현재 점수':** '요구 점수'는 선수가 최상의 경기력을 위해 스스로 필요하다고 생각하는 이상적인 목표 수준이다. '현재 점수'는 현재 자신의 상태에 대한 주관적인 평가다.
- **'훈련 요구량'의 중요성:** '요구 점수'와 '현재 점수'의 차이가 바로 '훈련 요구량'이다. 이 차이가 클수록 해당 항목에 대한 훈련의 우선순위가 높다는 것을 의미한다. 이상적인 상태는 이 차이가 2점 이하인 경우다.

### [매우 중요] 보고서 작성 지침:
- **데이터 기반 분석:** 너의 모든 분석과 제안은 반드시 아래에 제공된 '분석 데이터'의 항목들에만 근거해야 한다. **절대로 데이터에 없는 용어(예: 스윙, 서브 등)를 추측하거나 사용하지 마라.**
- **선수 지칭:** 보고서 전체에서 선수를 지칭할 때는 '김선수'와 같은 특정 이름 대신 '해당 선수' 또는 '선수'라는 용어를 사용하라.
- **형식 준수:** 아래의 [요약 보고서]와 [상세 보고서] 형식을 반드시 지켜서 응답하라.

---
### [요약 보고서]
- **[종합 평가]**: 현재 선수의 상태를 2~3 문장으로 명확하고 심도 있게 요약하라. 단순히 강점과 약점을 나열하는 것을 넘어, 두 요소가 어떻게 연결되는지 통합적으로 설명하라.
- **[주요 강점]**: **입력된 검사 항목 중에서**, 현재 점수가 필요 점수와 가장 근접하거나 초과하여 가장 잘하고 있는 핵심 강점 2가지를 키워드로 제시하라.
- **[주요 보완점]**: **입력된 검사 항목 중에서**, '요구 점수'와 '현재 점수'의 차이가 가장 커서 개선이 가장 시급한 핵심 보완점 2가지를 키워드로 제시하라.
---
### [상세 보고서]
1.  **[종합 분석 및 진단]**:
    - **총평:** 제공된 데이터 항목들을 바탕으로 선수의 현재 상태를 종합적으로 평가하라. 강점과 약점이 경기력에 어떻게 상호작용하고 있는지 심층적으로 설명하라.

2.  **[영역별 상세 분석]**:
    - **심리/멘탈 영역:** '자신감', '긴장조절', '집중력' 등 **데이터에 명시된** 심리 관련 항목들을 분석하라.
    - **기술(Skill) 영역:** '볼터치', '중거리슛', '패스' 등 **데이터에 명시된** 기술 관련 항목들을 분석하라.
    - **체력(Physical) 영역:** '지구력', '순발력' 등 **데이터에 명시된** 체력 관련 항목이 있다면 분석하라. (만약 없다면 이 부분은 생략 가능)

3.  **[솔루션 제시]**:
    - **핵심 문제 정의:** 위 분석을 바탕으로, 선수가 겪고 있을 가장 핵심적인 문제 상황을 구체적으로 정의하라.
    - **솔루션:** 정의된 핵심 문제를 해결하기 위한 다양하고 구체적인 솔루션을 심리적, 기술적, 체력적 관점을 통합하여 여러 가지 제안하라.

### 분석 데이터:
{data_str}
"""
    return prompt


def create_bar_chart(df):
    """
    분석 데이터를 바탕으로 비교 막대 그래프를 생성합니다.
    """
    df_melted = pd.melt(
        df,
        id_vars=["항목"],
        value_vars=["필요 점수", "현재 점수"],
        var_name="점수 유형",
        value_name="점수",
    )

    fig = px.bar(
        df_melted,
        x="항목",
        y="점수",
        color="점수 유형",
        barmode="group",
        title="<b>훈련 요구량 상위 항목 비교</b>",
        labels={
            "항목": "<b>평가 항목</b>",
            "점수": "<b>점수</b>",
            "점수 유형": "<b>점수 유형</b>",
        },
        text_auto=True,
        color_discrete_map={"필요 점수": "#636EFA", "현재 점수": "#FFA15A"},
    )

    fig.update_layout(
        font=dict(family="Arial, sans-serif", size=12),
        legend_title_text="",
        yaxis=dict(range=[0, 11]),
    )
    fig.update_traces(textposition="outside")
    return fig


# --- Streamlit UI 구성 ---

st.title("🧠 IZOF 멘탈 분석기 with Gemini")
st.markdown(
    "> IZOF(Individual Zones of Optimal Functioning) 이론을 바탕으로 당신의 멘탈 상태를 분석하고 맞춤형 훈련법을 제안합니다."
)
st.divider()

# --- 사이드바 ---
with st.sidebar:
    with st.expander("사용 방법 보기"):
        st.markdown("""
        1.  **'검사 결과 입력'** 칸에 **기술, 체력, 심리** 영역의 IZOF 검사 결과를 **모두** 붙여넣으세요.
        2.  **'분석하기'** 버튼을 클릭하여 AI의 요약 분석을 확인하세요.
        3.  **'상세 리포트 보기'** 버튼을 눌러 심층 분석 내용을 확인하세요.
        """)

# --- 메인 화면 ---
st.subheader("1. 검사 결과 입력")
placeholder_text = """# 기술, 체력, 심리 영역의 검사 결과를 모두 복사하여 아래에 붙여넣으세요.
# (항목 필요점수 현재점수)

# --- 예시 ---
# 기술
드라이버 정확도 8 6
퍼팅 자신감 9 7

# 체력
유산소 체력 9 10
순발력 8 7

# 심리
긴장 조절 7 5
승부욕 8 9
"""
user_input = st.text_area(
    "IZOF 검사 결과를 여기에 붙여넣으세요.", height=300, placeholder=placeholder_text
)

# "분석하기" 버튼
if st.button("🚀 분석하기", type="primary", use_container_width=True):
    if "GEMINI_API_KEY" not in os.environ:
        st.error("오류: 앱 관리자가 API 키를 설정하지 않았습니다.")
        st.stop()

    if not user_input:
        st.error("❗️ 분석할 데이터를 입력해주세요.")
    else:
        # 상태 초기화
        st.session_state.summary_report = None
        st.session_state.detailed_report = None
        st.session_state.chart_data = None
        st.session_state.show_report = False

        with st.spinner("AI가 당신의 멘탈 상태를 분석 중입니다..."):
            try:
                # 데이터 파싱 및 오늘 날짜 저장
                parsed_data = parse_data(user_input)
                kst = pytz.timezone("Asia/Seoul")
                st.session_state.analysis_date = datetime.now(kst).strftime("%Y-%m-%d")

                if not parsed_data:
                    st.error(
                        "❗️ 입력 데이터 형식을 확인해주세요. '항목 점수 점수' 형식으로 각 줄에 입력해야 합니다."
                    )
                else:
                    # Gemini 분석 실행
                    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    prompt = generate_analysis_prompt(parsed_data)
                    response = model.generate_content(prompt)

                    response_text = response.text
                    if "### [상세 보고서]" in response_text:
                        parts = response_text.split("### [상세 보고서]")
                        summary = parts[0].replace("### [요약 보고서]", "").strip()
                        detailed = "### [상세 보고서]\n" + parts[1].strip()
                    else:
                        summary = (
                            "요약 보고서를 생성하지 못했습니다. 전체 결과를 확인하세요."
                        )
                        detailed = response_text

                    # 그래프용 데이터 필터링
                    df = pd.DataFrame(parsed_data)
                    df["훈련 요구량"] = (df["필요 점수"] - df["현재 점수"]).abs()
                    chart_df = df.nlargest(5, "훈련 요구량")

                    # 결과 저장
                    st.session_state.summary_report = summary
                    st.session_state.detailed_report = detailed
                    st.session_state.chart_data = chart_df

            except Exception as e:
                st.error(f"⚠️ 분석 중 오류가 발생했습니다: {e}")

# --- 결과 출력 영역 ---
if st.session_state.summary_report:
    st.divider()
    st.subheader(f"해당 선수 AI 요약 분석 ({st.session_state.analysis_date})")

    if st.session_state.chart_data is not None:
        fig = create_bar_chart(st.session_state.chart_data)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown(st.session_state.summary_report)

    if st.button("📊 상세 리포트 보기", use_container_width=True):
        st.session_state.show_report = not st.session_state.show_report

if st.session_state.show_report and st.session_state.detailed_report:
    st.subheader("3. 상세 리포트")
    st.markdown(st.session_state.detailed_report)
