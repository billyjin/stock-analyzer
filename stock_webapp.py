"""
곡물 관련 주식 분석 웹앱
Streamlit을 사용한 인터랙티브 주식 분석 도구
"""

import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import time
warnings.filterwarnings('ignore')

# yfinance만 사용 (안정성을 위해)
FDR_AVAILABLE = False

# 페이지 설정
st.set_page_config(
    page_title="S&P 400 주식 분석기",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 매출 2조 이상 대기업 중심 섹터별 주식 분류
STOCK_SECTORS = {
    "🌾 농업/식품": {
        'WMT': '월마트',
        'COST': '코스트코',
        'DE': '디어앤컴퍼니 (John Deere)',
        'ADM': '아처 대니얼스 미들랜드',
        'BG': '번지',
        'GIS': '제너럴 밀스',
        'K': '켈로그',
        'TSN': '타이슨 푸드',
        'CTVA': '코르테바',
        'KR': '크로거',
        'SYY': '시스코 푸드',
        'MDLZ': '몬델리즈',
        'CPB': '캠벨 수프',
        'HRL': '호멜 푸드',
        'CAG': '콘아그라'
    },
    "🏭 산업/제조": {
        'CAT': '캐터필러',
        'BA': '보잉',
        'HON': '허니웰',
        'MMM': '3M',
        'GE': '제너럴 일렉트릭',
        'LMT': '록히드 마틴',
        'RTX': '레이시온 테크놀로지스',
        'UPS': 'UPS',
        'FDX': '페덱스',
        'NOC': '노스롭 그루먼',
        'EMR': '에머슨',
        'ITW': '일리노이 툴웍스',
        'DHR': '다나허',
        'ETN': '이튼',
        'PH': '파커 한니핀',
        'CMI': '커민스',
        'OTIS': '오티스',
        'CARR': '캐리어'
    },
    "🛒 소비재": {
        'AMZN': '아마존',
        'PG': '프록터앤갬블',
        'KO': '코카콜라',
        'PEP': '펩시코',
        'TGT': '타겟',
        'HD': '홈디포',
        'LOW': '로우스',
        'NKE': '나이키',
        'SBUX': '스타벅스',
        'MCD': '맥도날드',
        'DIS': '디즈니',
        'NFLX': '넷플릭스',
        'CL': '콜게이트',
        'KMB': '킴벌리클라크',
        'EL': '에스티로더',
        'TPG': '텍사스 퍼시픽',
        'GM': '제너럴모터스',
        'F': '포드'
    },
    "🏥 헬스케어": {
        'JNJ': '존슨앤존슨',
        'UNH': '유나이티드헬스',
        'PFE': '화이자',
        'ABT': '애보트',
        'MRK': '머크',
        'TMO': '써모 피셔',
        'CVS': 'CVS 헬스',
        'ABBV': '애브비',
        'LLY': '일라이 릴리',
        'BMY': '브리스톨마이어스',
        'AMGN': '암젠',
        'GILD': '길리어드',
        'MDT': '메드트로닉',
        'CI': '시그나',
        'ANTM': '앤썸',
        'HUM': '휴마나'
    },
    "💻 기술": {
        'AAPL': '애플',
        'MSFT': '마이크로소프트',
        'GOOGL': '알파벳 A',
        'GOOG': '알파벳 C',
        'META': '메타',
        'NVDA': '엔비디아',
        'TSLA': '테슬라',
        'CRM': '세일즈포스',
        'ORCL': '오라클',
        'ADBE': '어도비',
        'NFLX': '넷플릭스',
        'INTC': '인텔',
        'AMD': 'AMD',
        'QCOM': '퀄컴',
        'PYPL': '페이팔',
        'UBER': '우버',
        'SHOP': '쇼피파이',
        'ZM': '줌',
        'SNAP': '스냅챗'
    },
    "🏦 금융": {
        'BRK.B': '버크셔 해서웨이',
        'JPM': 'JP모건',
        'BAC': '뱅크오브아메리카',
        'WFC': '웰스파고',
        'GS': '골드만삭스',
        'MS': '모건스탠리',
        'C': '시티그룹',
        'AXP': '아메리칸익스프레스',
        'V': '비자',
        'MA': '마스터카드',
        'PYPL': '페이팔',
        'BLK': '블랙록',
        'SCHW': '찰스 슈왑',
        'USB': 'US 뱅코프',
        'PNC': 'PNC 파이낸셜',
        'TFC': '트루이스트'
    },
    "⚡ 에너지": {
        'XOM': '엑손모빌',
        'CVX': '셰브론',
        'COP': '코노코필립스',
        'EOG': 'EOG 리소시스',
        'SLB': '슐럼버거',
        'PSX': '필립스66',
        'VLO': '발레로',
        'MPC': '마라톤 페트롤리움',
        'OXY': '옥시덴탈',
        'BKR': '베이커 휴스',
        'HAL': '할리버튼',
        'DVN': '데본 에너지',
        'FANG': '다이아몬드백',
        'EQT': 'EQT',
        'KMI': '킨더 모건'
    },
    "🏠 부동산/REIT": {
        'AMT': '아메리칸타워',
        'PLD': '프롤로지스',
        'CCI': '크라운캐슬',
        'EQIX': '에쿼닉스',
        'PSA': '퍼블릭스토리지',
        'WELL': '웰타워',
        'DLR': '디지털 리얼티',
        'SBAC': 'SBA 커뮤니케이션',
        'O': '리얼티 인컴',
        'AVB': '아발론베이',
        'EQR': '에쿼티 레지덴셜',
        'VTR': '벤타스',
        'EXR': '익스텐디드스테이',
        'VICI': 'VICI 프로퍼티즈'
    },
    "🔌 유틸리티": {
        'NEE': '넥스트에라 에너지',
        'DUK': '듀크 에너지',
        'SO': '서던 컴퍼니',
        'D': '도미니언 에너지',
        'EXC': '엑셀론',
        'AEP': '아메리칸 일렉트릭',
        'XEL': '엑셀 에너지',
        'SRE': '셈프라 에너지',
        'PEG': 'PSEG',
        'ED': '콘에디슨',
        'EIX': '에디슨 인터내셔널',
        'WEC': 'WEC 에너지',
        'PPL': 'PPL',
        'FE': '퍼스트에너지'
    },
    "📱 통신/미디어": {
        'T': 'AT&T',
        'VZ': '버라이즌',
        'TMUS': 'T-모바일',
        'CHTR': '차터 커뮤니케이션',
        'CMCSA': '컴캐스트',
        'DIS': '디즈니',
        'NFLX': '넷플릭스',
        'PARA': '파라마운트',
        'WBD': '워너브라더스',
        'FOXA': '폭스 A',
        'FOX': '폭스',
        'DISH': '디쉬 네트워크',
        'LUMN': '루멘 테크놀로지스'
    }
}

# 전체 주식 리스트 (역순 매핑)
ALL_STOCKS = {}
for sector, stocks in STOCK_SECTORS.items():
    ALL_STOCKS.update(stocks)

@st.cache_data(ttl=3600*24)  # 24시간 캐시 (하루)
def fetch_stock_data_full(ticker, period='max'):
    """개별 주식의 전체 데이터를 가져오는 함수 (yfinance + 대체 소스)"""
    clean_ticker = ticker.strip().upper()
    if not clean_ticker:
        return None
    
    # 1차 시도: Yahoo Finance
    try:
        stock = yf.Ticker(clean_ticker)
        data = stock.history(period=period)
        
        # 데이터 유효성 검사
        if not data.empty and len(data) > 0 and 'Close' in data.columns:
            if not data['Close'].isna().all():
                return data
    except Exception as e:
        st.warning(f"⚠️ {clean_ticker}: Yahoo Finance 오류 - {str(e)}")
    
    # 2차 시도: FinanceDataReader 제거됨 (안정성을 위해 yfinance만 사용)
    # 3차 시도: 특정 티커 변환 시도 (CNHI 같은 경우)
    try:
        # 일부 티커는 다른 거래소나 형식으로 시도
        alternative_tickers = {
            'CNHI': 'CNH',  # CNH Industrial의 대체 티커
            'BRK.B': 'BRK-B',  # 버크셔 해서웨이 B 클래스
            'BF.B': 'BF-B'   # 브라운-포먼 B 클래스
        }
        
        if clean_ticker in alternative_tickers:
            alt_ticker = alternative_tickers[clean_ticker]
            stock = yf.Ticker(alt_ticker)
            data = stock.history(period=period)
            
            if not data.empty and len(data) > 0 and 'Close' in data.columns:
                if not data['Close'].isna().all():
                    st.info(f"✅ {clean_ticker}: 대체 티커 {alt_ticker}로 데이터 수집 성공")
                    return data
    except Exception:
        pass
    
    return None

def filter_data_by_date_range(data, start_date=None, end_date=None):
    """데이터를 날짜 범위로 필터링 (timezone 문제 해결)"""
    if data is None or data.empty:
        return data
    
    try:
        filtered_data = data.copy()
        
        if start_date:
            # timezone-aware 처리
            start_date = pd.to_datetime(start_date)
            if start_date.tz is None and hasattr(filtered_data.index, 'tz') and filtered_data.index.tz is not None:
                start_date = start_date.tz_localize(filtered_data.index.tz)
            elif start_date.tz is not None and (not hasattr(filtered_data.index, 'tz') or filtered_data.index.tz is None):
                start_date = start_date.tz_localize(None)
            
            filtered_data = filtered_data[filtered_data.index >= start_date]
        
        if end_date:
            # timezone-aware 처리
            end_date = pd.to_datetime(end_date)
            if end_date.tz is None and hasattr(filtered_data.index, 'tz') and filtered_data.index.tz is not None:
                end_date = end_date.tz_localize(filtered_data.index.tz)
            elif end_date.tz is not None and (not hasattr(filtered_data.index, 'tz') or filtered_data.index.tz is None):
                end_date = end_date.tz_localize(None)
            
            filtered_data = filtered_data[filtered_data.index <= end_date]
        
        return filtered_data
    except Exception as e:
        st.warning(f"⚠️ 날짜 필터링 오류: {str(e)} - 전체 데이터 사용")
        return data

def fetch_stock_data(tickers, period='10y', start_date=None, end_date=None):
    """
    스마트 캐싱을 적용한 주식 데이터 수집 함수
    - 전체 데이터를 캐시하고, 필요한 구간만 필터링
    """
    stock_data = {}
    failed_tickers = []
    cache_hits = 0
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, ticker in enumerate(tickers):
        try:
            status_text.text(f"📊 {ticker} 데이터 처리 중... ({i+1}/{len(tickers)})")
            
            clean_ticker = ticker.strip().upper()
            if not clean_ticker:
                continue
            
            # 1. 전체 데이터 가져오기 (캐시 활용)
            full_data = fetch_stock_data_full(clean_ticker, 'max')
            
            if full_data is not None:
                cache_hits += 1
                
                # 2. 사용자 지정 날짜 범위가 있으면 필터링
                if start_date or end_date:
                    filtered_data = filter_data_by_date_range(full_data, start_date, end_date)
                else:
                    # 3. 기본 period에 따라 필터링
                    if period != 'max':
                        # period를 날짜로 변환
                        if period == '1y':
                            period_start = datetime.now() - timedelta(days=365)
                        elif period == '2y':
                            period_start = datetime.now() - timedelta(days=365*2)
                        elif period == '5y':
                            period_start = datetime.now() - timedelta(days=365*5)
                        elif period == '10y':
                            period_start = datetime.now() - timedelta(days=365*10)
                        else:
                            period_start = None
                        
                        if period_start:
                            filtered_data = filter_data_by_date_range(full_data, period_start, None)
                        else:
                            filtered_data = full_data
                    else:
                        filtered_data = full_data
                
                # 최종 유효성 검사
                if not filtered_data.empty and len(filtered_data) > 0:
                    stock_data[clean_ticker] = filtered_data
                else:
                    failed_tickers.append(f"{clean_ticker} (필터링 후 데이터 없음)")
            else:
                failed_tickers.append(f"{clean_ticker} (데이터 수집 실패)")
            
            progress_bar.progress((i + 1) / len(tickers))
            
        except Exception as e:
            failed_tickers.append(f"{ticker} ({str(e)})")
            continue
    
    # 결과 표시
    if stock_data:
        status_text.text(f"✅ 데이터 처리 완료! ({len(stock_data)}개 성공, 캐시 활용: {cache_hits}개)")
    else:
        status_text.text("❌ 처리된 데이터가 없습니다")
    
    # 실패한 티커들 표시
    if failed_tickers:
        with st.expander(f"⚠️ 데이터 처리 실패 ({len(failed_tickers)}개)"):
            for failed in failed_tickers:
                st.text(f"• {failed}")
    
    progress_bar.empty()
    
    return stock_data

def normalize_prices(stock_data, start_value=100):
    """주가를 정규화하는 함수"""
    normalized_data = pd.DataFrame()
    
    for ticker, data in stock_data.items():
        if not data.empty:
            closing_prices = data['Close']
            normalized_prices = (closing_prices / closing_prices.iloc[0]) * start_value
            normalized_data[ticker] = normalized_prices
    
    return normalized_data

def min_max_scale(stock_data, date_range=None):
    """
    Min-Max 스케일링 함수 - 각 주식별로 개별적으로 0-1 범위로 스케일링
    
    Args:
        stock_data: 주식 데이터 딕셔너리 또는 DataFrame
        date_range: 스케일링 기준 날짜 범위 (tuple)
    
    Returns:
        DataFrame: 스케일링된 주가 데이터 (각 주식별로 0-1 범위)
    """
    scaled_data = pd.DataFrame()
    
    for ticker, data in stock_data.items():
        try:
            # 데이터가 Series인지 DataFrame인지 확인
            if isinstance(data, pd.Series):
                closing_prices = data
            elif isinstance(data, pd.DataFrame):
                if 'Close' in data.columns:
                    closing_prices = data['Close']
                else:
                    # Close 컬럼이 없으면 첫 번째 컬럼 사용
                    closing_prices = data.iloc[:, 0]
            else:
                st.warning(f"⚠️ {ticker}: 지원하지 않는 데이터 형식")
                continue
            
            # 빈 데이터 체크
            if closing_prices.empty or closing_prices.isna().all():
                st.warning(f"⚠️ {ticker}: 유효한 데이터가 없습니다")
                continue
            
            # NaN 값 제거
            closing_prices = closing_prices.dropna()
            
            if len(closing_prices) == 0:
                continue
            
            # 날짜 범위 지정시 해당 구간에서 min/max 계산
            if date_range and len(date_range) == 2:
                try:
                    start_date = pd.to_datetime(date_range[0])
                    end_date = pd.to_datetime(date_range[1])
                    
                    # timezone 처리
                    if start_date.tz is None and hasattr(closing_prices.index, 'tz') and closing_prices.index.tz is not None:
                        start_date = start_date.tz_localize(closing_prices.index.tz)
                        end_date = end_date.tz_localize(closing_prices.index.tz)
                    elif start_date.tz is not None and (not hasattr(closing_prices.index, 'tz') or closing_prices.index.tz is None):
                        start_date = start_date.tz_localize(None)
                        end_date = end_date.tz_localize(None)
                    
                    mask = (closing_prices.index >= start_date) & (closing_prices.index <= end_date)
                    range_data = closing_prices[mask]
                    
                    if not range_data.empty:
                        min_price = range_data.min()
                        max_price = range_data.max()
                    else:
                        # 지정 범위에 데이터가 없으면 전체 범위 사용
                        min_price = closing_prices.min()
                        max_price = closing_prices.max()
                except Exception as e:
                    st.warning(f"⚠️ {ticker}: 날짜 범위 처리 오류 ({str(e)}) - 전체 범위 사용")
                    min_price = closing_prices.min()
                    max_price = closing_prices.max()
            else:
                # 전체 기간 기준
                min_price = closing_prices.min()
                max_price = closing_prices.max()
            
            # Min-Max 스케일링 적용: (x - min) / (max - min)
            if max_price != min_price and not pd.isna(min_price) and not pd.isna(max_price):
                scaled_prices = (closing_prices - min_price) / (max_price - min_price)
                # 0-1 범위를 벗어나는 값 클리핑
                scaled_prices = scaled_prices.clip(0, 1)
                scaled_data[ticker] = scaled_prices
            else:
                # 모든 값이 동일한 경우 0.5로 설정
                scaled_data[ticker] = pd.Series([0.5] * len(closing_prices), index=closing_prices.index)
                
        except Exception as e:
            st.error(f"❌ {ticker} 스케일링 오류: {str(e)}")
            continue
    
    return scaled_data

def create_plotly_chart(data, title, y_label, chart_type="실주가", show_legend_controls=True, highlight_tickers=None):
    """Plotly를 사용한 인터랙티브 차트 생성"""
    
    # Legend 컨트롤 추가
    if show_legend_controls and len(data.columns) > 1:
        col_legend1, col_legend2, col_legend3 = st.columns([1, 1, 2])
        with col_legend1:
            if st.button("🔘 전체 선택", key=f"select_all_{hash(title)}"):
                st.session_state[f'legend_state_{hash(title)}'] = 'all_visible'
        with col_legend2:
            if st.button("⭕ 전체 해제", key=f"deselect_all_{hash(title)}"):
                st.session_state[f'legend_state_{hash(title)}'] = 'all_hidden'
        with col_legend3:
            if highlight_tickers:
                st.text(f"🎯 하이라이트: {len(highlight_tickers)}개 주식")
            else:
                st.text("💡 범례 클릭으로 개별 선택/해제 가능")
    
    fig = go.Figure()
    
    # 색상 팔레트 확장
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F', 
              '#FFB6C1', '#87CEEB', '#98FB98', '#F0E68C', '#DDA0DD', '#20B2AA', '#FF7F50', '#9370DB']
    
    # 하이라이트 색상 (더 진하고 굵게)
    highlight_colors = ['#FF0000', '#008080', '#0000FF', '#FF8C00', '#8B0000', '#4B0082', '#006400', '#DC143C']
    
    # Legend 상태 확인
    legend_state_key = f'legend_state_{hash(title)}'
    legend_state = st.session_state.get(legend_state_key, 'default')
    
    for i, (ticker, prices) in enumerate(data.items()):
        if not prices.empty:
            company_name = ALL_STOCKS.get(ticker, ticker)
            
            # 하이라이트 여부 확인
            is_highlighted = highlight_tickers and ticker in highlight_tickers
            
            # 색상 및 선 굵기 설정
            if is_highlighted:
                line_color = highlight_colors[i % len(highlight_colors)]
                line_width = 2
                opacity = 1.0
            else:
                line_color = colors[i % len(colors)]
                line_width = 1
                opacity = 0.7 if highlight_tickers else 1.0  # 하이라이트가 있으면 다른 라인들을 약간만 흐리게
            
            # Legend 상태에 따른 visibility 설정
            if legend_state == 'all_visible':
                visible = True
            elif legend_state == 'all_hidden':
                visible = 'legendonly'
            elif highlight_tickers:
                # 하이라이트 모드인 경우 - 비하이라이트 라인들도 legend에서 선택 가능하도록
                visible = True if is_highlighted else 'legendonly'
            else:
                visible = True  # 기본값
            
            # 이름에 하이라이트 표시 추가
            display_name = f'{ticker} - {company_name}'
            if is_highlighted:
                display_name = f'🎯 {display_name}'
            
            fig.add_trace(go.Scatter(
                x=prices.index,
                y=prices.values,
                mode='lines',
                name=display_name,
                line=dict(color=line_color, width=line_width),
                opacity=opacity,
                visible=visible,
                hovertemplate=f'<b>{ticker}</b><br>' +
                             f'날짜: %{{x}}<br>' +
                             f'{y_label}: %{{y:.2f}}<br>' +
                             '<extra></extra>'
            ))
    
    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(size=16)),
        xaxis_title="날짜",
        yaxis_title=y_label,
        hovermode='x unified',
        showlegend=True,
        height=600,
        template="plotly_white",
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="rgba(0,0,0,0.2)",
            borderwidth=1
        )
    )
    
    # 스케일링 차트인 경우 0-1 범위 표시 및 추가 정보
    if chart_type == "스케일링":
        fig.add_hline(y=0, line_dash="dash", line_color="red", opacity=0.5, 
                     annotation_text="최저점 (0)")
        fig.add_hline(y=1, line_dash="dash", line_color="green", opacity=0.5,
                     annotation_text="최고점 (1)")
        fig.add_hline(y=0.5, line_dash="dot", line_color="gray", opacity=0.3,
                     annotation_text="중간점 (0.5)")
        
        # Y축 범위를 0-1로 고정하고 적절한 마진 추가
        fig.update_yaxes(range=[-0.05, 1.05])
    
    # Legend 상태 초기화 (버튼 클릭 후)
    if legend_state != 'default':
        st.session_state[legend_state_key] = 'default'
    
    return fig

def calculate_performance_metrics(stock_data):
    """성과 지표 계산 (클러스터링용)"""
    metrics_data = []
    
    for ticker, data in stock_data.items():
        if not data.empty:
            prices = data['Close']
            start_price = prices.iloc[0]
            end_price = prices.iloc[-1]
            total_return = ((end_price - start_price) / start_price) * 100
            
            # 연간 수익률
            years = len(prices) / 252 if len(prices) > 252 else len(prices) / 252
            annual_return = ((end_price / start_price) ** (1/max(years, 0.1)) - 1) * 100
            
            # 분기 수익률 (최근 3개월)
            if len(prices) >= 63:  # 약 3개월 = 63 거래일
                quarterly_start = prices.iloc[-63]
                quarterly_return = ((end_price - quarterly_start) / quarterly_start) * 100
            else:
                quarterly_return = total_return
            
            # 변동성
            daily_returns = prices.pct_change().dropna()
            volatility = daily_returns.std() * np.sqrt(252) * 100
            
            metrics_data.append({
                'ticker': ticker,
                'company': ALL_STOCKS.get(ticker, ticker),
                'current_price': end_price,
                'total_return': total_return,
                'annual_return': annual_return,
                'quarterly_return': quarterly_return,
                'volatility': volatility
            })
    
    return metrics_data

def cluster_stocks_by_performance(metrics_data, n_clusters=4, clustering_basis='total'):
    """
    수익률 기반으로 주식을 클러스터링
    
    Args:
        metrics_data: 성과 지표 데이터
        n_clusters: 클러스터 개수
        clustering_basis: 클러스터링 기준 ('total', 'annual', 'quarterly')
    """
    if len(metrics_data) < n_clusters:
        n_clusters = len(metrics_data)
    
    # 클러스터링용 데이터 준비
    features = []
    tickers = []
    
    for metric in metrics_data:
        if clustering_basis == 'total':
            # 전체 기간 수익률 기준
            features.append([
                metric['total_return'],
                metric['volatility']  # 변동성도 고려
            ])
        elif clustering_basis == 'annual':
            # 연간 수익률 기준
            features.append([
                metric['annual_return'],
                metric['volatility']  # 변동성도 고려
            ])
        elif clustering_basis == 'quarterly':
            # 분기 수익률 기준
            features.append([
                metric['quarterly_return'],
                metric['volatility']  # 변동성도 고려
            ])
        else:
            # 복합 기준 (기본값)
            features.append([
                metric['total_return'],
                metric['annual_return'],
                metric['quarterly_return']
            ])
        
        tickers.append(metric['ticker'])
    
    if len(features) == 0:
        return [], []
    
    # 표준화
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)
    
    # K-means 클러스터링
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(features_scaled)
    
    # 클러스터별 그룹화
    clusters = {}
    for i, ticker in enumerate(tickers):
        cluster_id = cluster_labels[i]
        if cluster_id not in clusters:
            clusters[cluster_id] = []
        clusters[cluster_id].append({
            'ticker': ticker,
            'total_return': metrics_data[i]['total_return'],
            'annual_return': metrics_data[i]['annual_return'],
            'quarterly_return': metrics_data[i]['quarterly_return'],
            'volatility': metrics_data[i]['volatility']
        })
    
    # 클러스터를 선택된 기준에 따라 정렬
    sorted_clusters = []
    for cluster_id, stocks in clusters.items():
        if clustering_basis == 'total':
            avg_return = np.mean([stock['total_return'] for stock in stocks])
            return_type = '전체기간'
        elif clustering_basis == 'annual':
            avg_return = np.mean([stock['annual_return'] for stock in stocks])
            return_type = '연간'
        elif clustering_basis == 'quarterly':
            avg_return = np.mean([stock['quarterly_return'] for stock in stocks])
            return_type = '분기'
        else:
            avg_return = np.mean([stock['total_return'] for stock in stocks])
            return_type = '복합'
        
        sorted_clusters.append({
            'id': cluster_id,
            'avg_return': avg_return,
            'return_type': return_type,
            'stocks': stocks,
            'count': len(stocks)
        })
    
    sorted_clusters.sort(key=lambda x: x['avg_return'], reverse=True)
    
    return sorted_clusters, cluster_labels

def display_performance_metrics(stock_data):
    """성과 지표 표시 (숫자 정렬 가능)"""
    metrics_data = []
    
    for ticker, data in stock_data.items():
        if not data.empty:
            prices = data['Close']
            start_price = prices.iloc[0]
            end_price = prices.iloc[-1]
            total_return = ((end_price - start_price) / start_price) * 100
            
            # 연간 수익률
            years = len(prices) / 252
            annual_return = ((end_price / start_price) ** (1/years) - 1) * 100
            
            # 변동성
            daily_returns = prices.pct_change().dropna()
            volatility = daily_returns.std() * np.sqrt(252) * 100
            
            metrics_data.append({
                '티커': ticker,
                '회사명': ALL_STOCKS.get(ticker, ticker),
                '현재가': end_price,  # 숫자 그대로 저장
                '총수익률': total_return,  # 숫자 그대로 저장
                '연수익률': annual_return,  # 숫자 그대로 저장
                '변동성': volatility  # 숫자 그대로 저장
            })
    
    df = pd.DataFrame(metrics_data)
    
    # 숫자 컬럼들을 적절한 포맷으로 표시
    if not df.empty:
        df['현재가($)'] = df['현재가'].apply(lambda x: f"{x:.2f}")
        df['총 수익률(%)'] = df['총수익률'].apply(lambda x: f"{x:.1f}")
        df['연 수익률(%)'] = df['연수익률'].apply(lambda x: f"{x:.1f}")
        df['변동성(%)'] = df['변동성'].apply(lambda x: f"{x:.1f}")
        
        # 정렬용 숫자 컬럼 유지하면서 표시용 컬럼만 선택
        display_df = df[['티커', '회사명', '현재가($)', '총 수익률(%)', '연 수익률(%)', '변동성(%)']].copy()
        
        # 숫자 정렬을 위한 숨겨진 컬럼 추가
        display_df['_현재가_sort'] = df['현재가']
        display_df['_총수익률_sort'] = df['총수익률']
        display_df['_연수익률_sort'] = df['연수익률']
        display_df['_변동성_sort'] = df['변동성']
        
        return display_df
    
    return df

def main():
    # 메인 타이틀
    st.title("📈 S&P 400 주식 분석기")
    st.markdown("**10개 주요 섹터 • 80+ 대표 기업** | 실시간 데이터 분석 및 시각화")
    st.markdown("---")
    
    # 사이드바
    st.sidebar.header("🔧 설정")
    
    # 1. 분석 모드 선택
    analysis_mode = st.sidebar.radio(
        "분석 모드",
        ["섹터별 분석", "개별 주식 검색"]
    )
    
    selected_stocks = []
    
    if analysis_mode == "섹터별 분석":
        # 섹터 선택
        st.sidebar.subheader("📊 섹터 선택")
        
        # 전체 선택/해제 버튼
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("🔘 전체 선택", key="select_all"):
                st.session_state.selected_sectors = list(STOCK_SECTORS.keys())
        with col2:
            if st.button("⭕ 전체 해제", key="deselect_all"):
                st.session_state.selected_sectors = []
        
        # 세션 상태 초기화
        if 'selected_sectors' not in st.session_state:
            st.session_state.selected_sectors = ["🌾 농업/식품"]  # 기본값: 농업/식품만
        
        selected_sectors = st.sidebar.multiselect(
            "분석할 섹터를 선택하세요:",
            list(STOCK_SECTORS.keys()),
            default=st.session_state.selected_sectors,
            key="sector_multiselect"
        )
        
        # 선택된 섹터 수 표시
        total_stocks = sum(len(STOCK_SECTORS[sector]) for sector in selected_sectors)
        st.sidebar.info(f"📊 선택된 섹터: {len(selected_sectors)}개 | 총 주식: {total_stocks}개")
        
        # 선택된 섹터의 주식들
        for sector in selected_sectors:
            selected_stocks.extend(list(STOCK_SECTORS[sector].keys()))
    
    else:
        # 개별 주식 검색
        st.sidebar.subheader("🔍 주식 검색")
        
        # 섹터별 필터링
        filter_sector = st.sidebar.selectbox(
            "섹터 필터 (선택사항):",
            ["전체 섹터"] + list(STOCK_SECTORS.keys())
        )
        
        # 필터링된 주식 리스트
        if filter_sector == "전체 섹터":
            available_stocks = ALL_STOCKS
        else:
            available_stocks = STOCK_SECTORS[filter_sector]
        
        # 기본 주식 선택
        default_stocks = st.sidebar.multiselect(
            f"주식 선택 ({len(available_stocks)}개 중):",
            list(available_stocks.keys()),
            format_func=lambda x: f"{x} - {available_stocks[x]}",
            max_selections=20,  # 최대 20개 제한
            help="최대 20개까지 선택 가능합니다"
        )
        
        # 빠른 선택 버튼들
        st.sidebar.markdown("**🚀 빠른 선택:**")
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("🏆 유명 종목", key="famous_stocks"):
                default_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
        with col2:
            if st.button("🌾 농업 종목", key="agri_stocks"):
                default_stocks = ['DE', 'ADM', 'TSN', 'CTVA']
        
        # 커스텀 티커 입력
        custom_tickers = st.sidebar.text_input(
            "추가 티커 입력 (쉼표로 구분):",
            placeholder="예: TSLA, NFLX, AMD"
        )
        
        selected_stocks = default_stocks.copy()
        
        if custom_tickers:
            custom_list = [ticker.strip().upper() for ticker in custom_tickers.split(',')]
            selected_stocks.extend(custom_list)
        
        # 선택된 주식 수 표시
        st.sidebar.info(f"🎯 선택된 주식: {len(selected_stocks)}개")
    
    # 기간 설정
    st.sidebar.subheader("📅 분석 기간")
    
    period_mode = st.sidebar.radio(
        "기간 설정 방식:",
        ["기본 옵션", "사용자 지정"]
    )
    
    if period_mode == "기본 옵션":
        period = st.sidebar.selectbox(
            "기간 선택:",
            ["1y", "2y", "5y", "10y", "max"],
            index=3
        )
        # 기본 옵션에서는 날짜 범위를 None으로 설정
        custom_start_date = None
        custom_end_date = None
    else:
        # 사용자 지정 날짜 범위
        col1, col2 = st.sidebar.columns(2)
        with col1:
            custom_start_date = st.sidebar.date_input(
                "시작일", 
                datetime.now() - timedelta(days=365*5),  # 기본 5년 전
                max_value=datetime.now().date()
            )
        with col2:
            custom_end_date = st.sidebar.date_input(
                "종료일", 
                datetime.now().date(),
                max_value=datetime.now().date()
            )
        
        # 날짜 유효성 검사
        if custom_start_date >= custom_end_date:
            st.sidebar.error("❌ 시작일이 종료일보다 늦습니다!")
            custom_start_date = custom_end_date - timedelta(days=365)
        
        # 기간을 max로 설정하여 충분한 데이터 확보
        period = "max"
    
    # 차트 타입 선택
    st.sidebar.subheader("📊 차트 설정")
    chart_mode = st.sidebar.radio(
        "차트 표시 방식:",
        ["실주가", "정규화 (시작점=100)", "Min-Max 스케일링"]
    )
    
    # Min-Max 스케일링 옵션
    scaling_date_range = None
    if chart_mode == "Min-Max 스케일링":
        st.sidebar.subheader("🎯 스케일링 기준")
        scaling_mode = st.sidebar.radio(
            "스케일링 기준 구간:",
            ["전체 데이터 구간", "현재 표시 구간", "사용자 지정 구간"],
            help="사용자 지정 구간을 선택하면 해당 구간만 그래프에 표시됩니다"
        )
        
        if scaling_mode == "현재 표시 구간":
            # 현재 분석 구간을 스케일링 기준으로 사용
            if custom_start_date and custom_end_date:
                scaling_date_range = (custom_start_date, custom_end_date)
            else:
                scaling_date_range = None  # 기본 period 구간 사용
        elif scaling_mode == "사용자 지정 구간":
            col1, col2 = st.sidebar.columns(2)
            with col1:
                scale_start = st.sidebar.date_input(
                    "스케일링 시작일", 
                    datetime.now() - timedelta(days=365*2),
                    key="scale_start"
                )
            with col2:
                scale_end = st.sidebar.date_input(
                    "스케일링 종료일", 
                    datetime.now().date(),
                    key="scale_end"
                )
            
            if scale_start >= scale_end:
                st.sidebar.error("❌ 스케일링 시작일이 종료일보다 늦습니다!")
            else:
                scaling_date_range = (scale_start, scale_end)
        else:
            scaling_date_range = None  # 전체 데이터 구간 사용
    
    # 메인 컨텐츠
    if not selected_stocks:
        st.info("👈 사이드바에서 분석할 주식을 선택해주세요.")
        return
    
    st.subheader(f"📊 선택된 주식: {', '.join(selected_stocks)}")
    
    # 데이터 수집
    with st.spinner("📈 주가 데이터 처리 중..."):
        stock_data = fetch_stock_data(
            selected_stocks, 
            period, 
            start_date=custom_start_date, 
            end_date=custom_end_date
        )
    
    # 스케일링 모드 디버깅 정보
    if chart_mode == "Min-Max 스케일링" and scaling_mode == "사용자 지정 구간":
        if scaling_date_range:
            st.info(f"🎯 스케일링 모드: {scaling_mode} | 기준 구간: {scaling_date_range[0]} ~ {scaling_date_range[1]}")
        else:
            st.warning("⚠️ 사용자 지정 구간이 설정되지 않았습니다")
    
    if not stock_data:
        st.error("❌ 선택된 주식의 데이터를 가져올 수 없습니다.")
        return
    
    # 수익률 클러스터링 기준 선택
    st.sidebar.subheader("🎯 클러스터링 설정")
    clustering_basis = st.sidebar.radio(
        "수익률 클러스터링 기준:",
        ["전체 기간", "연간", "분기"],
        index=0,
        help="주식을 그룹화할 때 사용할 수익률 기준을 선택하세요"
    )
    
    # 기준을 코드로 변환
    basis_mapping = {
        "전체 기간": "total",
        "연간": "annual", 
        "분기": "quarterly"
    }
    basis_code = basis_mapping[clustering_basis]
    
    # 수익률 클러스터링 계산
    metrics_for_clustering = calculate_performance_metrics(stock_data)
    clusters, cluster_labels = cluster_stocks_by_performance(
        metrics_for_clustering, 
        n_clusters=4, 
        clustering_basis=basis_code
    )
    
    # 차트 생성
    col1, col2 = st.columns([3, 1])
    
    # 하이라이트할 주식들 가져오기 (세션 상태에서 안전하게)
    highlight_tickers = st.session_state.get('highlight_tickers', None)
    
    # 강제 리렌더링을 위한 상태 확인
    if 'force_rerender' not in st.session_state:
        st.session_state['force_rerender'] = 0
    
    with col1:
        if chart_mode == "실주가":
            # 실주가 차트
            closing_data = pd.DataFrame({ticker: data['Close'] for ticker, data in stock_data.items()})
            fig = create_plotly_chart(
                closing_data, 
                "주가 추이 (실주가)", 
                "주가 (USD)", 
                "실주가",
                highlight_tickers=highlight_tickers
            )
            
        elif chart_mode == "정규화 (시작점=100)":
            # 정규화 차트
            normalized_data = normalize_prices(stock_data, 100)
            fig = create_plotly_chart(
                normalized_data, 
                "주가 추이 (정규화)", 
                "정규화 주가 (시작점=100)", 
                "정규화",
                highlight_tickers=highlight_tickers
            )
            
        else:  # Min-Max 스케일링
            try:
                # stock_data에서 직접 스케일링 (사용자 지정 날짜 범위 적용)
                scaled_data = min_max_scale(stock_data, scaling_date_range)
                
                # 스케일링 기준에 따라 그래프 표시 구간도 조정
                display_data = scaled_data.copy()
                
                # 사용자 지정 구간인 경우 해당 구간만 표시
                if scaling_mode == "사용자 지정 구간" and scaling_date_range:
                    try:
                        start_date = pd.to_datetime(scaling_date_range[0])
                        end_date = pd.to_datetime(scaling_date_range[1])
                        
                        # 각 주식별로 날짜 범위 필터링
                        filtered_display_data = pd.DataFrame()
                        for ticker in display_data.columns:
                            ticker_data = display_data[ticker].dropna()
                            
                            # timezone 처리
                            if start_date.tz is None and hasattr(ticker_data.index, 'tz') and ticker_data.index.tz is not None:
                                start_date_adj = start_date.tz_localize(ticker_data.index.tz)
                                end_date_adj = end_date.tz_localize(ticker_data.index.tz)
                            elif start_date.tz is not None and (not hasattr(ticker_data.index, 'tz') or ticker_data.index.tz is None):
                                start_date_adj = start_date.tz_localize(None)
                                end_date_adj = end_date.tz_localize(None)
                            else:
                                start_date_adj = start_date
                                end_date_adj = end_date
                            
                            mask = (ticker_data.index >= start_date_adj) & (ticker_data.index <= end_date_adj)
                            filtered_ticker_data = ticker_data[mask]
                            if not filtered_ticker_data.empty:
                                filtered_display_data[ticker] = filtered_ticker_data
                        
                        if not filtered_display_data.empty:
                            display_data = filtered_display_data
                            st.info(f"📊 표시 구간: {scaling_date_range[0]} ~ {scaling_date_range[1]} ({len(filtered_display_data.index)}일)")
                        else:
                            st.warning("⚠️ 지정된 구간에 데이터가 없습니다. 전체 구간 표시")
                    except Exception as filter_error:
                        st.error(f"❌ 구간 필터링 오류: {str(filter_error)} - 전체 구간 표시")
                
                # 스케일링 기준 정보 표시
                if scaling_date_range:
                    scale_info = f" (기준: {scaling_date_range[0]} ~ {scaling_date_range[1]})"
                    if scaling_mode == "사용자 지정 구간":
                        scale_info += " [표시구간 일치]"
                else:
                    scale_info = " (기준: 전체 구간)"
                
                fig = create_plotly_chart(
                    display_data, 
                    f"주가 추이 (Min-Max 스케일링){scale_info}", 
                    "스케일링된 주가 (0-1)", 
                    "스케일링",
                    highlight_tickers=highlight_tickers
                )
            except Exception as e:
                st.error(f"❌ 스케일링 처리 오류: {str(e)}")
                # 대안으로 정규화 차트 표시
                normalized_data = normalize_prices(stock_data, 100)
                fig = create_plotly_chart(
                    normalized_data, 
                    "주가 추이 (정규화 - 스케일링 오류로 대체)", 
                    "정규화 주가", 
                    "정규화",
                    highlight_tickers=highlight_tickers
                )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 수익률 클러스터링
        st.subheader(f"🎯 수익률 클러스터 ({clustering_basis})")
        if clusters and len(clusters) > 1:
            # 클러스터링 기준에 따른 수익률 표시
            cluster_options = []
            for i, cluster in enumerate(clusters):
                avg_return = cluster['avg_return']
                return_type = cluster['return_type']
                stock_list = [stock['ticker'] for stock in cluster['stocks']]
                cluster_label = f"그룹 {i+1}: {avg_return:.1f}% {return_type} ({len(stock_list)}개)"
                cluster_options.append((cluster_label, stock_list, cluster))
            
            selected_cluster = st.selectbox(
                f"수익률 그룹 선택 ({clustering_basis} 기준):",
                ["전체"] + [option[0] for option in cluster_options],
                help="특정 그룹을 선택하면 해당 주식들만 하이라이트됩니다",
                key=f"cluster_selectbox_{clustering_basis}"
            )
            
            # 클러스터 상세 정보 및 세션 상태 즉시 업데이트
            if selected_cluster != "전체":
                cluster_idx = [option[0] for option in cluster_options].index(selected_cluster)
                selected_stocks_in_cluster = cluster_options[cluster_idx][1]
                cluster_info = cluster_options[cluster_idx][2]
                
                # 세션 상태 변경 체크 및 즉시 업데이트
                if st.session_state.get('selected_cluster') != selected_cluster:
                    st.session_state['highlight_tickers'] = selected_stocks_in_cluster
                    st.session_state['selected_cluster'] = selected_cluster
                    st.rerun()
                
                st.info(f"📌 선택된 그룹: {', '.join(selected_stocks_in_cluster)}")
                # 그룹 내 상세 정보 표시
                st.markdown("**📊 그룹 상세 정보:**")
                # 데이터프레임으로 깔끔하게 표시
                group_data = []
                for stock in cluster_info['stocks']:
                    company_name = ALL_STOCKS.get(stock['ticker'], stock['ticker'])
                    group_data.append({
                        '티커': stock['ticker'],
                        '회사명': company_name,
                        '전체 수익률(%)': f"{stock['total_return']:.1f}",
                        '연간 수익률(%)': f"{stock['annual_return']:.1f}",
                        '분기 수익률(%)': f"{stock['quarterly_return']:.1f}"
                    })
                
                group_df = pd.DataFrame(group_data)
                st.dataframe(
                    group_df, 
                    use_container_width=True, 
                    hide_index=True,
                    height=150,  # 높이 제한으로 공간 절약
                    column_config={
                        "전체 수익률(%)": st.column_config.NumberColumn(
                            "전체 수익률(%)",
                            help="전체 기간 수익률",
                            format="%.1f"
                        ),
                        "연간 수익률(%)": st.column_config.NumberColumn(
                            "연간 수익률(%)",
                            help="연환산 수익률", 
                            format="%.1f"
                        ),
                        "분기 수익률(%)": st.column_config.NumberColumn(
                            "분기 수익률(%)",
                            help="최근 3개월 수익률",
                            format="%.1f"
                        )
                    }
                )
            else:
                # 전체 선택 시 하이라이트 해제
                if st.session_state.get('selected_cluster') != "전체":
                    st.session_state['highlight_tickers'] = None
                    st.session_state['selected_cluster'] = "전체"
                    st.rerun()
        else:
            st.info("클러스터링을 위해서는 최소 2개 이상의 주식이 필요합니다.")
            st.session_state['highlight_tickers'] = None
        
        # 성과 지표
        st.subheader("📊 성과 지표")
        metrics_df = display_performance_metrics(stock_data)
        
        # 정렬 옵션 추가
        if not metrics_df.empty:
            sort_options = {
                '티커': '티커',
                '현재가': '_현재가_sort',
                '총 수익률': '_총수익률_sort', 
                '연 수익률': '_연수익률_sort',
                '변동성': '_변동성_sort'
            }
            
            col_sort1, col_sort2 = st.columns(2)
            with col_sort1:
                sort_by = st.selectbox("정렬 기준:", list(sort_options.keys()), index=2, key="sort_by")
            with col_sort2:
                sort_ascending = st.radio("정렬 방향:", ["내림차순", "오름차순"], index=0, key="sort_dir") == "오름차순"
            
            # 정렬 적용
            if sort_by in sort_options:
                sort_column = sort_options[sort_by]
                if sort_column in metrics_df.columns:
                    metrics_df_sorted = metrics_df.sort_values(sort_column, ascending=sort_ascending)
                else:
                    metrics_df_sorted = metrics_df.sort_values(sort_by, ascending=sort_ascending)
            else:
                metrics_df_sorted = metrics_df
            
            # 숨겨진 정렬 컬럼 제거하고 표시
            display_columns = ['티커', '회사명', '현재가($)', '총 수익률(%)', '연 수익률(%)', '변동성(%)']
            st.dataframe(
                metrics_df_sorted[display_columns], 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "총 수익률(%)": st.column_config.NumberColumn(
                        "총 수익률(%)",
                        help="전체 기간 수익률",
                        format="%.1f"
                    ),
                    "연 수익률(%)": st.column_config.NumberColumn(
                        "연 수익률(%)", 
                        help="연환산 수익률",
                        format="%.1f"
                    ),
                    "변동성(%)": st.column_config.NumberColumn(
                        "변동성(%)",
                        help="연환산 변동성",
                        format="%.1f"
                    ),
                    "현재가($)": st.column_config.NumberColumn(
                        "현재가($)",
                        help="현재 주가",
                        format="%.2f"
                    )
                }
            )
        else:
            st.dataframe(metrics_df, use_container_width=True, hide_index=True)
    
    # 섹터별 분석인 경우 섹터별 차트도 표시
    if analysis_mode == "섹터별 분석" and len(selected_sectors) > 1:
        st.markdown("---")
        st.subheader("🏭 섹터별 상세 분석")
        
        tabs = st.tabs(selected_sectors)
        
        for i, sector in enumerate(selected_sectors):
            with tabs[i]:
                sector_stocks = list(STOCK_SECTORS[sector].keys())
                sector_data = {ticker: stock_data[ticker] for ticker in sector_stocks if ticker in stock_data}
                
                if sector_data:
                    if chart_mode == "실주가":
                        sector_closing = pd.DataFrame({ticker: data['Close'] for ticker, data in sector_data.items()})
                        sector_fig = create_plotly_chart(
                            sector_closing, 
                            f"{sector} 섹터 주가 추이", 
                            "주가 (USD)", 
                            "실주가",
                            highlight_tickers=highlight_tickers
                        )
                    elif chart_mode == "정규화 (시작점=100)":
                        sector_normalized = normalize_prices(sector_data, 100)
                        sector_fig = create_plotly_chart(
                            sector_normalized, 
                            f"{sector} 섹터 주가 추이 (정규화)", 
                            "정규화 주가", 
                            "정규화",
                            highlight_tickers=highlight_tickers
                        )
                    else:
                        try:
                            sector_scaled = min_max_scale(sector_data, scaling_date_range)
                            
                            # 섹터별 표시 데이터 조정
                            sector_display_data = sector_scaled.copy()
                            
                            # 사용자 지정 구간인 경우 해당 구간만 표시
                            if scaling_mode == "사용자 지정 구간" and scaling_date_range:
                                try:
                                    start_date = pd.to_datetime(scaling_date_range[0])
                                    end_date = pd.to_datetime(scaling_date_range[1])
                                    
                                    # 각 주식별로 날짜 범위 필터링
                                    filtered_sector_data = pd.DataFrame()
                                    for ticker in sector_display_data.columns:
                                        ticker_data = sector_display_data[ticker].dropna()
                                        
                                        # timezone 처리
                                        if start_date.tz is None and hasattr(ticker_data.index, 'tz') and ticker_data.index.tz is not None:
                                            start_date_adj = start_date.tz_localize(ticker_data.index.tz)
                                            end_date_adj = end_date.tz_localize(ticker_data.index.tz)
                                        elif start_date.tz is not None and (not hasattr(ticker_data.index, 'tz') or ticker_data.index.tz is None):
                                            start_date_adj = start_date.tz_localize(None)
                                            end_date_adj = end_date.tz_localize(None)
                                        else:
                                            start_date_adj = start_date
                                            end_date_adj = end_date
                                        
                                        mask = (ticker_data.index >= start_date_adj) & (ticker_data.index <= end_date_adj)
                                        filtered_ticker_data = ticker_data[mask]
                                        if not filtered_ticker_data.empty:
                                            filtered_sector_data[ticker] = filtered_ticker_data
                                    
                                    if not filtered_sector_data.empty:
                                        sector_display_data = filtered_sector_data
                                except Exception as e:
                                    st.warning(f"⚠️ {sector} 섹터 필터링 오류: {str(e)}")
                            
                            # 스케일링 기준 정보
                            if scaling_date_range:
                                scale_info = f" (기준: {scaling_date_range[0]} ~ {scaling_date_range[1]})"
                                if scaling_mode == "사용자 지정 구간":
                                    scale_info += " [표시구간 일치]"
                            else:
                                scale_info = " (기준: 전체 구간)"
                            
                            sector_fig = create_plotly_chart(
                                sector_display_data, 
                                f"{sector} 섹터 주가 추이 (스케일링){scale_info}", 
                                "스케일링된 주가", 
                                "스케일링",
                                highlight_tickers=highlight_tickers
                            )
                        except Exception as e:
                            st.warning(f"⚠️ {sector} 섹터 스케일링 오류: {str(e)}")
                            # 대안으로 정규화 차트 표시
                            sector_normalized = normalize_prices(sector_data, 100)
                            sector_fig = create_plotly_chart(
                                sector_normalized, 
                                f"{sector} 섹터 주가 추이 (정규화)", 
                                "정규화 주가", 
                                "정규화",
                                highlight_tickers=highlight_tickers
                            )
                    
                    st.plotly_chart(sector_fig, use_container_width=True)
                    
                    # 섹터 성과 지표
                    sector_metrics = display_performance_metrics(sector_data)
                    st.dataframe(sector_metrics, use_container_width=True, hide_index=True)
    
    # 정보 패널
    st.markdown("---")
    with st.expander("ℹ️ 도움말"):
        st.markdown("""
        ### 📖 사용법
        
        **1. 분석 모드**
        - **섹터별 분석**: 농업 관련 섹터를 선택하여 해당 섹터 주식들을 분석
        - **개별 주식 검색**: 특정 주식을 직접 선택하거나 티커를 입력하여 분석
        
        **2. 기간 설정**
        - **기본 옵션**: 1년, 2년, 5년, 10년, 전체 기간 중 선택
        - **사용자 지정**: 시작일과 종료일을 직접 지정
        
        **3. 차트 표시 방식**
        - **실주가**: 실제 주가로 표시
        - **정규화**: 시작점을 100으로 설정하여 상대적 수익률 비교
        - **Min-Max 스케일링**: 0-1 범위로 스케일링하여 변동 패턴 비교
        
        **4. Min-Max 스케일링 기준 구간**
        - **전체 데이터 구간**: 각 주식의 전체 기간 중 최고/최저점 기준 (전체 그래프 표시)
        - **현재 표시 구간**: 현재 차트에 표시되는 기간의 최고/최저점 기준
        - **사용자 지정 구간**: 사용자가 직접 지정한 기간의 최고/최저점 기준 (**해당 구간만 그래프 표시**)
        
        **5. Min-Max 스케일링 공식**
        ```
        스케일값 = (현재주가 - 구간최소주가) / (구간최대주가 - 구간최소주가)
        ```
        
        **🎯 스케일링 결과:**
        - 각 주식별로 **개별적으로** 0-1 범위로 정규화
        - 최저점 = 0, 최고점 = 1
        - 모든 주식이 동일한 스케일로 변동 패턴 비교 가능
        
        ### 📊 포함된 섹터 (S&P 400 위주)
        - **🌾 농업/식품**: DE, CNHI, ADM, BG, GIS, K, TSN, CTVA (8개)
        - **🏭 산업/제조**: CAT, HON, MMM, GE, LMT, RTX, UPS, FDX (8개)
        - **🛒 소비재**: PG, KO, PEP, WMT, TGT, HD, LOW, NKE (8개)
        - **🏥 헬스케어**: JNJ, PFE, ABT, MRK, UNH, CVS, WBA, GILD (8개)
        - **💻 기술**: AAPL, MSFT, GOOGL, AMZN, META, NVDA, CRM, ADBE (8개)
        - **🏦 금융**: JPM, BAC, WFC, GS, MS, AXP, V, MA (8개)
        - **⚡ 에너지**: XOM, CVX, COP, SLB, EOG, PXD, KMI, OKE (8개)
        - **🏠 부동산/REIT**: AMT, PLD, CCI, EQIX, PSA, EXR, AVB, EQR (8개)
        - **🔌 유틸리티**: NEE, DUK, SO, D, EXC, XEL, SRE, AEP (8개)
        - **📱 통신**: T, VZ, TMUS, CHTR, CMCSA, VIA, DISH, LUMN (8개)
        
        ### 🎯 수익률 클러스터링
        - **전체 기간**: 투자 시작부터 현재까지의 총 수익률 기준
        - **연간**: 연환산 수익률 기준으로 그룹화
        - **분기**: 최근 3개월 수익률 기준으로 그룹화
        - 각 그룹 선택 시 해당 주식들만 차트에서 하이라이트
        
        ### 💡 팁
        - 차트는 인터랙티브하므로 확대, 축소, 범례 클릭 등이 가능합니다
        - **🔘 전체 선택 / ⭕ 전체 해제** 버튼으로 모든 라인 제어 가능
        - **스마트 캐싱**: 전체 데이터는 24시간 동안 캐시되어 날짜 변경 시 즉시 반영됩니다
        - 커스텀 티커 입력시 정확한 심볼을 입력해주세요
        - 사용자 지정 기간으로 특정 구간만 상세 분석이 가능합니다
        - 성과지표 테이블은 숫자 기준으로 정확한 정렬이 가능합니다
        """)

if __name__ == "__main__":
    main()
