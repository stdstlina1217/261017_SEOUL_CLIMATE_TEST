import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="서울 연평균 기온 분석", page_icon="🌡️", layout="wide")

# ---------- 데이터 로드 ----------
@st.cache_data
def load_data():
    df = pd.read_csv("seoul_temperature.csv", encoding="utf-8-sig")

    # 1) 날짜 앞 탭 문자 제거 후 datetime 변환
    df["날짜"] = df["날짜"].astype(str).str.strip()
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")

    # 2) 서울 지점(108) 데이터만 사용
    df = df[df["지점"] == 108]

    # 3) 수치 컬럼 변환
    num_cols = ["평균기온(℃)", "최저기온(℃)", "최고기온(℃)"]
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 4) 결측값 제외 (1950-1953 등)
    before = len(df)
    df = df.dropna(subset=["날짜"] + num_cols)
    st.sidebar.metric("데이터 행 수", f"{before:,} → {len(df):,}")
    return df

df = load_data()

# ---------- 연도 추출 및 연도별 집계 ----------
df["연도"] = df["날짜"].dt.year

yearly = (
    df.groupby("연도")
    .agg(
        연평균기온=("평균기온(℃)", "mean"),
        연평균최고기온=("최고기온(℃)", "mean"),
        연평균최저기온=("최저기온(℃)", "mean"),
    )
    .reset_index()
)

# 5년 이동평균(연도별 평균기온 기준)
yearly["5년기온이동평균"] = yearly["연평균기온"].rolling(window=5, min_periods=5).mean()

# ---------- 사이드바: 연도 범위 슬라이더 ----------
min_year, max_year = int(yearly["연도"].min()), int(yearly["연도"].max())
year_range = st.sidebar.slider(
    "연도 범위", min_value=min_year, max_value=max_year, value=(min_year, max_year)
)
st.sidebar.caption(f"선택 구간: {year_range[0]}년 ~ {year_range[1]}년")

# 선택 구간 필터링
sel = yearly[(yearly["연도"] >= year_range[0]) & (yearly["연도"] <= year_range[1])]

# ---------- 본문 ----------
st.title("서울 연평균 기온 분석")
st.caption("1950-1953 등 결측값을 제외한 데이터로 분석했습니다.")

# 1·2. 연평균기온 + 5년 이동평균 꺾은선 그래프
fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=sel["연도"],
        y=sel["연평균기온"],
        mode="lines+markers",
        name="연평균기온",
        line=dict(color="#1f77b4", width=2),
    )
)
fig.add_trace(
    go.Scatter(
        x=sel["연도"],
        y=sel["5년기온이동평균"],
        mode="lines+markers",
        name="5년 이동평균",
        line=dict(color="#d62728", width=2, dash="dash"),
    )
)
fig.update_layout(
    title="서울 연평균기온과 5년 이동평균",
    xaxis_title="연도",
    yaxis_title="기온 (℃)",
    hovermode="x unified",
    margin=dict(l=40, r=20, t=40, b=30),
)
st.plotly_chart(fig, use_container_width=True)

# 3·4. 선택 구간의 평균·최고·최저 기온
if not sel.empty:
    col1, col2, col3 = st.columns(3)
    col1.metric("평균기온 평균", f"{sel['연평균기온'].mean():.2f} ℃")
    col2.metric("최고기온 평균", f"{sel['연평균최고기온'].mean():.2f} ℃")
    col3.metric("최저기온 평균", f"{sel['연평균최저기온'].mean():.2f} ℃")

    st.subheader("선택 구간 연도별 통계")
    st.dataframe(
        sel[["연도", "연평균기온", "연평균최고기온", "연평균최저기온"]],
        use_container_width=True,
    )
