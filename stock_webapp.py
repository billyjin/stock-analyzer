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
import os
import re
import io
import json
from typing import List, Dict
from ticker_management import TickerManager, ticker_management_ui
from persistent_storage import initialize_persistent_storage
from volatility_analysis import VOLATILITY_ANALYZER, KOREAN_SMALL_CAP_SYMBOLS
from stock_cache import STOCK_CACHE
from stock_lists import STOCK_LIST_MANAGER
warnings.filterwarnings('ignore')

# yfinance만 사용 (안정성을 위해)
FDR_AVAILABLE = False

# 페이지 설정
st.set_page_config(
    page_title="통합 금융 분석기",
    page_icon="📊",
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

# 티커 관리자 인스턴스
TICKER_MANAGER = TickerManager()

def get_combined_stock_list():
    """기본 주식 + 커스텀 주식 통합 리스트 반환"""
    combined_stocks = {}
    
    # 기본 주식들
    for sector, stocks in STOCK_SECTORS.items():
        if sector not in combined_stocks:
            combined_stocks[sector] = {}
        combined_stocks[sector].update(stocks)
    
    # 커스텀 주식들 추가
    if 'custom_tickers' in st.session_state:
        for ticker, info in st.session_state.custom_tickers.items():
            sector = info['sector']
            name = info['name']
            
            if sector not in combined_stocks:
                combined_stocks[sector] = {}
            combined_stocks[sector][ticker] = name
    
    return combined_stocks

def get_all_stocks_flat():
    """모든 주식을 평면적으로 반환 (역순 매핑)"""
    all_stocks = {}
    combined_list = get_combined_stock_list()
    
    for sector, stocks in combined_list.items():
        all_stocks.update(stocks)
    
    return all_stocks

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
                opacity = 0.9  # 하이라이트된 라인들을 약간 덜 진하게
            else:
                line_color = colors[i % len(colors)]
                line_width = 1
                opacity = 0.8 if highlight_tickers else 1.0  # 비하이라이트 라인들을 더 잘 보이게
            
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
        try:
            df['현재가($)'] = df['현재가'].apply(lambda x: f"{float(x):.2f}" if pd.notna(x) else "N/A")
            df['총 수익률(%)'] = df['총수익률'].apply(lambda x: f"{float(x):.1f}" if pd.notna(x) else "N/A")
            df['연 수익률(%)'] = df['연수익률'].apply(lambda x: f"{float(x):.1f}" if pd.notna(x) else "N/A")
            df['변동성(%)'] = df['변동성'].apply(lambda x: f"{float(x):.1f}" if pd.notna(x) else "N/A")
        except Exception as e:
            print(f"포맷팅 오류: {e}")
            # 포맷팅 실패 시 기본값 사용
            df['현재가($)'] = df['현재가'].astype(str)
            df['총 수익률(%)'] = df['총수익률'].astype(str)
            df['연 수익률(%)'] = df['연수익률'].astype(str)
            df['변동성(%)'] = df['변동성'].astype(str)
        
        # 정렬용 숫자 컬럼 유지하면서 표시용 컬럼만 선택
        display_df = df[['티커', '회사명', '현재가($)', '총 수익률(%)', '연 수익률(%)', '변동성(%)']].copy()
        
        # 숫자 정렬을 위한 숨겨진 컬럼 추가
        display_df['_현재가_sort'] = df['현재가']
        display_df['_총수익률_sort'] = df['총수익률']
        display_df['_연수익률_sort'] = df['연수익률']
        display_df['_변동성_sort'] = df['변동성']
        
        return display_df
    
    return df

# ================== 매크로 경제 데이터 분석 함수들 ==================

@st.cache_data(ttl=3600)  # 1시간 캐시
def load_macro_data():
    """Excel 파일에서 매크로 경제 데이터를 로드합니다."""
    try:
        if not os.path.exists('macro_data_trimmed.xlsx'):
            st.error("❌ macro_data_trimmed.xlsx 파일을 찾을 수 없습니다.")
            return None, None
        
        # Raw_month_USD scale 시트 (0~1 스케일된 데이터)
        scaled_data = pd.read_excel('macro_data_trimmed.xlsx', sheet_name='Raw_month_USD scale')
        
        # Raw_month_USD base 시트 (원본 값 데이터)
        base_data = pd.read_excel('macro_data_trimmed.xlsx', sheet_name='Raw_month_USD base')
        
        # 숫자가 아닌 컬럼 제거 및 숫자 변환
        def clean_numeric_data(df):
            # 첫 번째 컬럼(날짜)을 제외하고 숫자 변환
            for col in df.columns:
                if col != df.columns[0]:  # 첫 번째 컬럼(날짜) 제외
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            return df
        
        scaled_data = clean_numeric_data(scaled_data)
        base_data = clean_numeric_data(base_data)
        
        # 인덱스를 날짜로 설정 (첫 번째 열이 날짜라고 가정)
        if scaled_data.columns[0] in ['Date', 'date', 'DATE']:
            scaled_data.set_index(scaled_data.columns[0], inplace=True)
            base_data.set_index(base_data.columns[0], inplace=True)
        else:
            # 첫 번째 열을 날짜로 가정
            scaled_data.set_index(scaled_data.columns[0], inplace=True)
            base_data.set_index(base_data.columns[0], inplace=True)
        
        # 인덱스를 datetime으로 변환
        scaled_data.index = pd.to_datetime(scaled_data.index)
        base_data.index = pd.to_datetime(base_data.index)
        
        return scaled_data, base_data
        
    except Exception as e:
        st.error(f"❌ 데이터 로드 오류: {str(e)}")
        return None, None

def create_macro_timeseries_chart(data, features, title, chart_type="원본값"):
    """매크로 경제 지표의 시계열 차트를 생성합니다."""
    if data is None or data.empty:
        st.warning("표시할 데이터가 없습니다.")
        return None
    
    fig = go.Figure()
    
    # 색상 팔레트
    colors = px.colors.qualitative.Set3
    
    for i, feature in enumerate(features):
        if feature in data.columns:
            fig.add_trace(go.Scatter(
                x=data.index,
                y=data[feature],
                mode='lines',
                name=feature,
                line=dict(color=colors[i % len(colors)], width=2),
                hovertemplate=f'<b>{feature}</b><br>' +
                             'Date: %{x}<br>' +
                             'Value: %{y:.4f}<extra></extra>'
            ))
    
    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            font=dict(size=16, family="Arial Black")
        ),
        xaxis_title="날짜",
        yaxis_title="값" if chart_type == "원본값" else "스케일된 값 (0-1)",
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=500,
        template="plotly_white"
    )
    
    # 스케일된 데이터인 경우 Y축 범위 설정
    if chart_type == "스케일값":
        fig.update_yaxes(range=[-0.05, 1.05])
        # 참조선 추가
        fig.add_hline(y=0, line_dash="dash", line_color="red", opacity=0.5)
        fig.add_hline(y=1, line_dash="dash", line_color="green", opacity=0.5)
        fig.add_hline(y=0.5, line_dash="dot", line_color="gray", opacity=0.3)
    
    return fig

def macro_analysis_page():
    """매크로 경제 분석 페이지"""
    st.title("📊 매크로 경제 지표 분석")
    st.markdown("**시계열 데이터 분석** | Excel 데이터 기반 매크로 경제 트렌드")
    
    # 데이터 로드
    scaled_data, base_data = load_macro_data()
    
    if scaled_data is None or base_data is None:
        st.error("데이터를 로드할 수 없습니다. macro_data_trimmed.xlsx 파일을 확인해주세요.")
        return
    
    # 사이드바 설정
    st.sidebar.header("📊 분석 설정")
    
    # 데이터 유형 선택
    data_type = st.sidebar.radio(
        "데이터 유형:",
        ["원본값 (Raw)", "스케일값 (0-1)"],
        help="원본값: 실제 경제지표 값, 스케일값: 0-1로 정규화된 값"
    )
    
    current_data = base_data if data_type == "원본값 (Raw)" else scaled_data
    
    # 지표 선택
    available_features = list(current_data.columns)
    
    st.sidebar.subheader("📈 분석할 지표 선택")
    
    # 전체 선택/해제 버튼
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🔘 전체 선택"):
            st.session_state['selected_features'] = available_features
    with col2:
        if st.button("⭕ 전체 해제"):
            st.session_state['selected_features'] = []
    
    # 초기값 설정
    if 'selected_features' not in st.session_state:
        st.session_state['selected_features'] = available_features[:5]  # 처음 5개만 선택
    
    selected_features = st.sidebar.multiselect(
        "경제 지표 선택:",
        available_features,
        default=st.session_state.get('selected_features', available_features[:5]),
        help="분석하고 싶은 경제 지표들을 선택하세요"
    )
    
    # 날짜 범위 설정
    st.sidebar.subheader("📅 분석 기간")
    min_date = current_data.index.min().date()
    max_date = current_data.index.max().date()
    
    start_date = st.sidebar.date_input(
        "시작일:",
        value=min_date,
        min_value=min_date,
        max_value=max_date
    )
    
    end_date = st.sidebar.date_input(
        "종료일:",
        value=max_date,
        min_value=min_date,
        max_value=max_date
    )
    
    # 데이터 필터링
    mask = (current_data.index.date >= start_date) & (current_data.index.date <= end_date)
    filtered_data = current_data.loc[mask]
    
    if selected_features:
        # 메인 컨텐츠 영역
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # 전체 지표 통합 차트
            if len(selected_features) > 0:
                chart_title = f"📈 매크로 경제 지표 시계열 분석 ({data_type})"
                chart_type = "스케일값" if data_type == "스케일값 (0-1)" else "원본값"
                
                fig = create_macro_timeseries_chart(
                    filtered_data, 
                    selected_features, 
                    chart_title,
                    chart_type
                )
                
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # 통계 정보
            st.subheader("📊 기본 통계")
            
            try:
                # 숫자 데이터로 변환
                numeric_data = filtered_data[selected_features].apply(pd.to_numeric, errors='coerce')
                stats_data = numeric_data.describe()
                st.dataframe(
                    stats_data.round(4),
                    use_container_width=True,
                    height=300
                )
            except Exception as e:
                st.warning(f"⚠️ 통계 계산 오류: {str(e)}")
                st.info("💡 데이터가 숫자 형식이 아닐 수 있습니다.")
            
            # 상관관계 매트릭스
            if len(selected_features) > 1:
                st.subheader("🔄 상관관계")
                try:
                    # 데이터를 숫자 형태로 변환하고 NaN 제거
                    numeric_data = filtered_data[selected_features].apply(pd.to_numeric, errors='coerce')
                    numeric_data = numeric_data.dropna()
                    
                    if not numeric_data.empty and len(numeric_data) > 1:
                        corr_matrix = numeric_data.corr()
                        
                        fig_corr = px.imshow(
                            corr_matrix,
                            text_auto=True,
                            aspect="auto",
                            color_continuous_scale="RdBu_r",
                            title="상관관계 매트릭스"
                        )
                        fig_corr.update_layout(height=400)
                        st.plotly_chart(fig_corr, use_container_width=True)
                    else:
                        st.warning("⚠️ 상관관계 계산을 위한 충분한 숫자 데이터가 없습니다.")
                except Exception as e:
                    st.warning(f"⚠️ 상관관계 계산 오류: {str(e)}")
                    st.info("💡 일부 데이터가 숫자가 아닐 수 있습니다.")
        
        # 개별 지표 상세 분석
        if st.checkbox("📋 개별 지표 상세 분석", value=False):
            st.markdown("---")
            st.subheader("📋 개별 지표 상세 분석")
            
            # 지표별 개별 차트 (2열로 배치)
            cols = st.columns(2)
            
            for i, feature in enumerate(selected_features):
                with cols[i % 2]:
                    # 개별 차트
                    individual_fig = create_macro_timeseries_chart(
                        filtered_data, 
                        [feature], 
                        f"📊 {feature}",
                        chart_type
                    )
                    
                    if individual_fig:
                        st.plotly_chart(individual_fig, use_container_width=True)
                    
                    # 기본 통계
                    try:
                        numeric_feature_data = pd.to_numeric(filtered_data[feature], errors='coerce')
                        feature_stats = numeric_feature_data.describe()
                        st.write(f"**{feature} 통계:**")
                        stat_cols = st.columns(3)
                        with stat_cols[0]:
                            st.metric("평균", f"{feature_stats['mean']:.4f}")
                        with stat_cols[1]:
                            st.metric("표준편차", f"{feature_stats['std']:.4f}")
                        with stat_cols[2]:
                            latest_value = numeric_feature_data.iloc[-1]
                            if pd.notna(latest_value):
                                st.metric("최신값", f"{latest_value:.4f}")
                            else:
                                st.metric("최신값", "N/A")
                    except Exception as e:
                        st.warning(f"⚠️ {feature} 통계 계산 오류: {str(e)}")
        
        # 데이터 테이블
        if st.checkbox("📊 원본 데이터 보기", value=False):
            st.markdown("---")
            st.subheader("📊 원본 데이터")
            
            # 최신 데이터부터 표시
            display_data = filtered_data[selected_features].sort_index(ascending=False)
            st.dataframe(
                display_data,
                use_container_width=True,
                height=400
            )
            
            # 데이터 다운로드
            csv = display_data.to_csv().encode('utf-8')
            st.download_button(
                label="📥 CSV 다운로드",
                data=csv,
                file_name=f"macro_data_{data_type}_{start_date}_{end_date}.csv",
                mime="text/csv"
            )
    
    else:
        st.warning("분석할 경제 지표를 선택해주세요.")
    
    # 정보 패널
    st.markdown("---")
    with st.expander("ℹ️ 매크로 데이터 정보"):
        st.markdown("""
        ### 📖 매크로 경제 지표 분석 도구
        
        **데이터 소스**: macro_data_trimmed.xlsx
        - **Raw_month_USD base**: 원본 경제지표 값
        - **Raw_month_USD scale**: 0-1로 정규화된 값 (비교 분석 용이)
        
        ### 🔧 주요 기능
        - **시계열 분석**: 각 경제지표의 시간별 변화 추이
        - **상관관계 분석**: 지표 간 상호 연관성 분석
        - **정규화 비교**: 스케일이 다른 지표들의 트렌드 비교
        - **통계 분석**: 기본 통계량 및 변동성 분석
        
        ### 💡 활용 팁
        - **스케일값**: 서로 다른 단위의 지표들을 동일한 기준으로 비교
        - **상관관계**: 경제지표 간의 연관성을 파악하여 트렌드 예측
        - **개별 분석**: 특정 지표의 상세한 변화 패턴 분석
        """)

def stock_analysis_page():
    """기존 주식 분석 페이지"""
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
        
        # 통합 주식 리스트 사용
        combined_stocks = get_combined_stock_list()
        
        # 전체 선택/해제 버튼
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("🔘 전체 선택", key="select_all"):
                st.session_state.selected_sectors = list(combined_stocks.keys())
        with col2:
            if st.button("⭕ 전체 해제", key="deselect_all"):
                st.session_state.selected_sectors = []
        
        # 세션 상태 초기화
        if 'selected_sectors' not in st.session_state:
            st.session_state.selected_sectors = ["🌾 농업/식품"]  # 기본값: 농업/식품만
        
        selected_sectors = st.sidebar.multiselect(
            "분석할 섹터를 선택하세요:",
            list(combined_stocks.keys()),
            default=st.session_state.selected_sectors,
            key="sector_multiselect"
        )
        
        # 선택된 섹터 수 표시
        total_stocks = sum(len(combined_stocks[sector]) for sector in selected_sectors)
        
        # 커스텀 티커 수 계산
        custom_count = 0
        if 'custom_tickers' in st.session_state:
            for sector in selected_sectors:
                custom_count += sum(1 for ticker, info in st.session_state.custom_tickers.items() 
                                  if info['sector'] == sector)
        
        st.sidebar.info(f"📊 선택된 섹터: {len(selected_sectors)}개 | 총 주식: {total_stocks}개 (커스텀: {custom_count}개)")
        
        # 선택된 섹터의 주식들
        for sector in selected_sectors:
            selected_stocks.extend(list(combined_stocks[sector].keys()))
    
    else:
        # 개별 주식 검색
        st.sidebar.subheader("🔍 주식 검색")
        
        # 통합 주식 리스트 사용
        combined_stocks = get_combined_stock_list()
        all_stocks_flat = get_all_stocks_flat()
        
        # 섹터별 필터링
        filter_sector = st.sidebar.selectbox(
            "섹터 필터 (선택사항):",
            ["전체 섹터"] + list(combined_stocks.keys())
        )
        
        # 필터링된 주식 리스트
        if filter_sector == "전체 섹터":
            available_stocks = all_stocks_flat
        else:
            available_stocks = combined_stocks[filter_sector]
        
        # 기본 주식 선택
        default_stocks = st.sidebar.multiselect(
            f"주식 선택 ({len(available_stocks)}개 중):",
            list(available_stocks.keys()),
            format_func=lambda x: f"{x} - {available_stocks[x]}",
            max_selections=30,  # 최대 30개로 증가
            help="최대 30개까지 선택 가능합니다"
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
        
        # 스마트 티커 입력 (자동 검증 및 분류)
        st.sidebar.markdown("**🔧 스마트 티커 추가:**")
        smart_ticker_input = st.sidebar.text_input(
            "티커 입력 (자동 검증):",
            placeholder="예: NVDA (자동 섹터 분류)",
            key="smart_ticker"
        )
        
        if smart_ticker_input:
            ticker = smart_ticker_input.strip().upper()
            is_valid, error_msg, stock_info = TICKER_MANAGER.validate_ticker(ticker)
            
            if is_valid:
                sector = TICKER_MANAGER.classify_sector(ticker, stock_info)
                st.sidebar.success(f"✅ {ticker} → {sector}")
                
                if st.sidebar.button(f"➕ {ticker} 추가", key="add_smart_ticker"):
                    success, message = TICKER_MANAGER.add_ticker(ticker)
                    if success:
                        st.sidebar.success("추가됨!")
                        st.rerun()
            else:
                st.sidebar.error(f"❌ {error_msg}")
        
        # 기존 커스텀 티커 입력 (호환성 유지)
        custom_tickers = st.sidebar.text_input(
            "추가 티커 입력 (쉼표로 구분):",
            placeholder="예: TSLA, NFLX, AMD"
        )
        
        selected_stocks = default_stocks.copy()
        
        if custom_tickers:
            custom_list = [ticker.strip().upper() for ticker in custom_tickers.split(',')]
            selected_stocks.extend(custom_list)
        
        # 선택된 주식 수 표시
        custom_count = len([t for t in selected_stocks if t in st.session_state.get('custom_tickers', {})])
        st.sidebar.info(f"🎯 선택된 주식: {len(selected_stocks)}개 (커스텀: {custom_count}개)")
    
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

def volatility_analysis_page():
    """잡주 변동성 분석 페이지"""
    st.title("🎯 잡주(소형주/테마주) 변동성 분석")
    st.markdown("---")
    
    # 탭으로 구성
    tab1, tab2, tab3 = st.tabs(["📊 변동성 분석", "📋 주식 리스트 관리", "🗂️ 캐시 관리"])
    
    with tab1:
        # 분석 설명
        st.markdown("""
        ### 📊 **잡주 분석 개요**
        
        이 도구는 다음 지표들을 종합하여 잡주의 변동성을 분석합니다:
        
        - **🌍 VIX (변동성 지수)**: 글로벌 시장 공포도 측정
        - **📈 KOSPI/KOSDAQ 변동성**: 한국 시장 변동성 추이
        - **🔍 소형주 스크리닝**: 시가총액, 거래량, 변동성 기준
        - **📊 기술적 지표**: ATR, 볼린저밴드, RSI 등
        - **💡 시장 심리**: 투자자 심리 및 리스크 레벨
        """)
        
        # 분석 옵션
        col1, col2, col3 = st.columns(3)
        
        with col1:
            analysis_type = st.selectbox(
                "분석 유형 선택",
                ["실시간 변동성 분석", "소형주 스크리닝", "시장 심리 분석", "종합 분석"],
                help="원하는 분석 유형을 선택하세요"
            )
        
        with col2:
            market_selection = st.selectbox(
                "시장 선택",
                ["한국 소형주", "한국 테마주", "한국 잡주 후보", "미국 소형주", "미국 잡주 후보", "미국 밈주식", "전체"],
                help="분석할 주식 시장을 선택하세요"
            )
        
        with col3:
            max_stocks = st.slider(
                "분석할 최대 종목 수",
                min_value=5, max_value=50, value=20,
                help="분석할 소형주의 최대 개수를 설정하세요"
            )
        
        # 변동성 지수 분석 기간 선택 (실시간 변동성 분석일 때만)
        if analysis_type == "실시간 변동성 분석":
            st.markdown("### 📅 변동성 지수 분석 기간")
            period_col1, period_col2 = st.columns(2)
            
            with period_col1:
                vix_period = st.selectbox(
                    "VIX/SKEW 히스토리 기간",
                    ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
                    index=2,  # 기본값: 6mo
                    help="VIX와 SKEW 지수의 트렌드를 볼 기간을 선택하세요"
                )
            
            with period_col2:
                period_description = {
                    "1mo": "1개월 - 최근 단기 트렌드",
                    "3mo": "3개월 - 분기별 변화",
                    "6mo": "6개월 - 중기 트렌드 (권장)",
                    "1y": "1년 - 연간 사이클",
                    "2y": "2년 - 중장기 패턴",
                    "5y": "5년 - 장기 히스토리"
                }
                st.info(f"**선택된 기간**: {period_description[vix_period]}")
        else:
            vix_period = "6mo"  # 다른 분석 유형의 기본값
        
        # 주식 리스트 선택
        def get_symbols_by_selection(market_selection: str) -> List[str]:
            """시장 선택에 따른 심볼 리스트 반환"""
            if market_selection == "한국 소형주":
                return list(STOCK_LIST_MANAGER.get_korean_stocks("small_cap").keys())
            elif market_selection == "한국 테마주":
                return list(STOCK_LIST_MANAGER.get_korean_stocks("theme_stocks").keys())
            elif market_selection == "한국 잡주 후보":
                return list(STOCK_LIST_MANAGER.get_korean_stocks("speculation_candidates").keys())
            elif market_selection == "미국 소형주":
                return list(STOCK_LIST_MANAGER.get_us_stocks("small_cap").keys())
            elif market_selection == "미국 잡주 후보":
                return list(STOCK_LIST_MANAGER.get_us_stocks("speculation_candidates").keys())
            elif market_selection == "미국 밈주식":
                meme_stocks = STOCK_LIST_MANAGER.get_us_stocks("speculation_candidates", "meme")
                return list(meme_stocks.keys()) if meme_stocks else []
            elif market_selection == "전체":
                korean_stocks = list(STOCK_LIST_MANAGER.get_korean_stocks().keys())
                us_stocks = list(STOCK_LIST_MANAGER.get_us_stocks().keys())
                return korean_stocks + us_stocks
            else:
                return []
        
        symbols_to_analyze = get_symbols_by_selection(market_selection)
        
        st.markdown("---")
        
        # 선택된 종목 정보
        st.markdown(f"**📋 선택된 종목**: {len(symbols_to_analyze)}개 (상위 {max_stocks}개 분석 예정)")
        
        # 분석할 종목 미리보기
        if symbols_to_analyze:
            preview_symbols = symbols_to_analyze[:min(10, len(symbols_to_analyze))]
            preview_info = []
            for symbol in preview_symbols:
                stock_info = STOCK_LIST_MANAGER.find_stock_info(symbol)
                preview_info.append(f"**{symbol}** ({stock_info.get('name', 'Unknown')})")
            
            st.markdown("**🔍 분석 예정 종목 (미리보기)**:")
            st.markdown(" • ".join(preview_info))
            if len(symbols_to_analyze) > 10:
                st.markdown(f"... 외 {len(symbols_to_analyze) - 10}개")
        
        st.markdown("---")
    
    # 분석 실행 버튼
    if st.button("🔍 잡주 분석 시작", type="primary"):
        
        with st.spinner("변동성 지수 및 소형주 데이터를 수집하고 있습니다..."):
            
            try:
                # 종합 분석 실행
                if analysis_type == "종합 분석":
                    # 선택된 심볼로 종합 분석 실행
                    analysis_result = VOLATILITY_ANALYZER.comprehensive_volatility_analysis(
                        symbols_to_analyze[:max_stocks]
                    )
                    
                    # 결과 표시
                    display_comprehensive_analysis(analysis_result)
                    
                elif analysis_type == "실시간 변동성 분석":
                    # 변동성 지수만 분석 (사용자 선택 기간 적용)
                    st.info(f"📊 {period_description[vix_period]} 기간으로 VIX/SKEW 데이터를 분석합니다...")
                    volatility_indices = VOLATILITY_ANALYZER.get_volatility_indices(period=vix_period)
                    market_sentiment = VOLATILITY_ANALYZER.analyze_market_sentiment(volatility_indices)
                    
                    display_volatility_indices(volatility_indices, market_sentiment)
                    
                elif analysis_type == "소형주 스크리닝":
                    # 선택된 심볼로 소형주 탐지 실행
                    small_caps = VOLATILITY_ANALYZER.detect_small_cap_stocks(
                        symbols_to_analyze[:max_stocks],
                        max_market_cap=5e11,  # 5000억원
                        min_volatility=20.0
                    )
                    
                    display_small_cap_screening(small_caps)
                    
                elif analysis_type == "시장 심리 분석":
                    # 시장 심리만 분석
                    volatility_indices = VOLATILITY_ANALYZER.get_volatility_indices(period="1mo")
                    market_sentiment = VOLATILITY_ANALYZER.analyze_market_sentiment(volatility_indices)
                    
                    display_market_sentiment(market_sentiment, volatility_indices)
                    
            except Exception as e:
                st.error(f"분석 중 오류가 발생했습니다: {str(e)}")
                st.info("일부 데이터를 가져올 수 없을 때 발생할 수 있습니다. 잠시 후 다시 시도해주세요.")
                
                # 개발자용 상세 오류 정보
                if st.checkbox("🔧 개발자 모드: 상세 오류 보기"):
                    import traceback
                    st.code(traceback.format_exc())
    
    with tab2:
        # 주식 리스트 관리
        display_stock_list_management()
    
    with tab3:
        # 캐시 관리
        display_cache_management()

def get_symbols_by_selection(market_selection: str) -> List[str]:
    """시장 선택에 따른 심볼 리스트 반환"""
    if market_selection == "한국 소형주":
        return list(STOCK_LIST_MANAGER.get_korean_stocks("small_cap").keys())
    elif market_selection == "한국 테마주":
        return list(STOCK_LIST_MANAGER.get_korean_stocks("theme_stocks").keys())
    elif market_selection == "한국 잡주 후보":
        return list(STOCK_LIST_MANAGER.get_korean_stocks("speculation_candidates").keys())
    elif market_selection == "미국 소형주":
        return list(STOCK_LIST_MANAGER.get_us_stocks("small_cap").keys())
    elif market_selection == "미국 잡주 후보":
        return list(STOCK_LIST_MANAGER.get_us_stocks("speculation_candidates").keys())
    elif market_selection == "미국 밈주식":
        meme_stocks = STOCK_LIST_MANAGER.get_us_stocks("small_cap", "meme_stocks")
        reddit_stocks = STOCK_LIST_MANAGER.get_us_stocks("speculation_candidates", "reddit_favorites")
        return list(set(list(meme_stocks.keys()) + list(reddit_stocks.keys())))
    else:  # 전체
        korean_small = list(STOCK_LIST_MANAGER.get_korean_stocks("small_cap").keys())
        korean_theme = list(STOCK_LIST_MANAGER.get_korean_stocks("theme_stocks").keys())
        korean_spec = list(STOCK_LIST_MANAGER.get_korean_stocks("speculation_candidates").keys())
        us_small = list(STOCK_LIST_MANAGER.get_us_stocks("small_cap").keys())
        us_spec = list(STOCK_LIST_MANAGER.get_us_stocks("speculation_candidates").keys())
        return list(set(korean_small + korean_theme + korean_spec + us_small + us_spec))

def display_stock_list_management():
    """주식 리스트 관리 UI"""
    st.subheader("📋 주식 리스트 관리")
    
    # 통계 정보
    stats = STOCK_LIST_MANAGER.get_stats()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("전체 종목 수", stats['total_stocks'])
    with col2:
        korean_data = stats['by_market'].get('korean_stocks', {})
        korean_count = 0
        if isinstance(korean_data, dict):
            for category_data in korean_data.values():
                if isinstance(category_data, dict):
                    korean_count += sum(category_data.values())
                else:
                    korean_count += category_data
        st.metric("한국 종목", korean_count)
    with col3:
        us_data = stats['by_market'].get('us_stocks', {})
        us_count = 0
        if isinstance(us_data, dict):
            for category_data in us_data.values():
                if isinstance(category_data, dict):
                    us_count += sum(category_data.values())
                else:
                    us_count += category_data
        st.metric("미국 종목", us_count)
    
    st.markdown("---")
    
    # 카테고리별 현황 테이블
    st.subheader("📊 카테고리별 현황")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🇰🇷 한국 주식")
        korean_stocks = STOCK_LIST_MANAGER.get_korean_stocks()
        
        if korean_stocks:
            # 카테고리별로 그룹화
            korean_by_category = {}
            for symbol, info in korean_stocks.items():
                category = info.get('category', 'unknown')
                subcategory = info.get('subcategory', 'default')
                
                if category not in korean_by_category:
                    korean_by_category[category] = {}
                if subcategory not in korean_by_category[category]:
                    korean_by_category[category][subcategory] = []
                
                korean_by_category[category][subcategory].append({
                    'symbol': symbol,
                    'name': info.get('name', 'N/A')
                })
            
            # 테이블 데이터 생성
            korean_category_data = []
            for category, subcategories in korean_by_category.items():
                for subcategory, stocks in subcategories.items():
                    # 티커 리스트 생성 (심볼(종목명) 형태)
                    ticker_list = []
                    for stock in stocks:
                        if stock['name'] != 'N/A':
                            ticker_list.append(f"{stock['symbol']}({stock['name']})")
                        else:
                            ticker_list.append(stock['symbol'])
                    
                    korean_category_data.append({
                        '카테고리': category,
                        '서브카테고리': subcategory,
                        '종목 수': len(stocks),
                        '티커 리스트': ', '.join(ticker_list)
                    })
            
            korean_df = pd.DataFrame(korean_category_data)
            st.dataframe(
                korean_df, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "티커 리스트": st.column_config.TextColumn(
                        "티커 리스트",
                        help="카테고리에 포함된 모든 종목",
                        width="large"
                    )
                }
            )
        else:
            st.info("등록된 한국 주식이 없습니다.")
    
    with col2:
        st.markdown("#### 🇺🇸 미국 주식")
        us_stocks = STOCK_LIST_MANAGER.get_us_stocks()
        
        if us_stocks:
            # 카테고리별로 그룹화
            us_by_category = {}
            for symbol, info in us_stocks.items():
                category = info.get('category', 'unknown')
                subcategory = info.get('subcategory', 'default')
                
                if category not in us_by_category:
                    us_by_category[category] = {}
                if subcategory not in us_by_category[category]:
                    us_by_category[category][subcategory] = []
                
                us_by_category[category][subcategory].append({
                    'symbol': symbol,
                    'name': info.get('name', 'N/A')
                })
            
            # 테이블 데이터 생성
            us_category_data = []
            for category, subcategories in us_by_category.items():
                for subcategory, stocks in subcategories.items():
                    # 티커 리스트 생성 (심볼(종목명) 형태)
                    ticker_list = []
                    for stock in stocks:
                        if stock['name'] != 'N/A':
                            ticker_list.append(f"{stock['symbol']}({stock['name']})")
                        else:
                            ticker_list.append(stock['symbol'])
                    
                    us_category_data.append({
                        '카테고리': category,
                        '서브카테고리': subcategory,
                        '종목 수': len(stocks),
                        '티커 리스트': ', '.join(ticker_list)
                    })
            
            us_df = pd.DataFrame(us_category_data)
            st.dataframe(
                us_df, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "티커 리스트": st.column_config.TextColumn(
                        "티커 리스트",
                        help="카테고리에 포함된 모든 종목",
                        width="large"
                    )
                }
            )
        else:
            st.info("등록된 미국 주식이 없습니다.")
    
    # 전체 리스트 다운로드/업로드 기능
    st.markdown("---")
    st.subheader("📥📤 잡주 리스트 다운로드/업로드")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📥 현재 리스트 다운로드")
        
        # 전체 주식 리스트를 DataFrame으로 변환
        all_stocks_data = []
        
        # 한국 주식 추가
        korean_stocks = STOCK_LIST_MANAGER.get_korean_stocks()
        for symbol, info in korean_stocks.items():
            all_stocks_data.append({
                '시장': 'korean_stocks',
                '카테고리': info.get('category', ''),
                '서브카테고리': info.get('subcategory', ''),
                '심볼': symbol,
                '종목명': info.get('name', '')
            })
        
        # 미국 주식 추가
        us_stocks = STOCK_LIST_MANAGER.get_us_stocks()
        for symbol, info in us_stocks.items():
            all_stocks_data.append({
                '시장': 'us_stocks',
                '카테고리': info.get('category', ''),
                '서브카테고리': info.get('subcategory', ''),
                '심볼': symbol,
                '종목명': info.get('name', '')
            })
        
        if all_stocks_data:
            download_df = pd.DataFrame(all_stocks_data)
            
            # Excel 파일로 다운로드
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                download_df.to_excel(writer, sheet_name='잡주리스트', index=False)
            excel_buffer.seek(0)
            
            st.download_button(
                label="📊 Excel 파일 다운로드",
                data=excel_buffer.getvalue(),
                file_name=f"잡주리스트_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            # CSV 파일로 다운로드
            csv_buffer = io.StringIO()
            download_df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
            csv_buffer.seek(0)
            
            st.download_button(
                label="📄 CSV 파일 다운로드",
                data=csv_buffer.getvalue(),
                file_name=f"잡주리스트_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            
            # 미리보기
            st.markdown("##### 📋 다운로드 미리보기")
            st.dataframe(download_df.head(10), use_container_width=True, hide_index=True)
            if len(download_df) > 10:
                st.info(f"총 {len(download_df)}개 종목 중 10개만 미리보기")
        else:
            st.warning("다운로드할 주식 데이터가 없습니다.")
    
    with col2:
        st.markdown("#### 📤 수정된 리스트 업로드")
        
        # 템플릿 다운로드
        template_data = [
            {
                '시장': 'korean_stocks',
                '카테고리': 'small_cap',
                '서브카테고리': 'IT',
                '심볼': '000000',
                '종목명': '예시종목'
            },
            {
                '시장': 'us_stocks',
                '카테고리': 'speculation_candidates',
                '서브카테고리': 'meme',
                '심볼': 'EXAMPLE',
                '종목명': 'Example Stock'
            }
        ]
        template_df = pd.DataFrame(template_data)
        
        template_buffer = io.BytesIO()
        with pd.ExcelWriter(template_buffer, engine='openpyxl') as writer:
            template_df.to_excel(writer, sheet_name='템플릿', index=False)
        template_buffer.seek(0)
        
        st.download_button(
            label="📋 템플릿 다운로드",
            data=template_buffer.getvalue(),
            file_name="잡주리스트_템플릿.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        # 파일 업로드
        uploaded_file = st.file_uploader(
            "수정된 잡주 리스트 업로드",
            type=['xlsx', 'csv'],
            help="Excel 또는 CSV 파일을 업로드하세요"
        )
        
        if uploaded_file is not None:
            try:
                # 파일 읽기
                if uploaded_file.name.endswith('.xlsx'):
                    upload_df = pd.read_excel(uploaded_file)
                else:
                    upload_df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
                
                # 필수 컬럼 확인
                required_columns = ['시장', '카테고리', '서브카테고리', '심볼', '종목명']
                if not all(col in upload_df.columns for col in required_columns):
                    st.error(f"필수 컬럼이 없습니다: {', '.join(required_columns)}")
                else:
                    st.success(f"✅ 파일 업로드 성공! ({len(upload_df)}개 종목)")
                    
                    # 업로드된 데이터 미리보기
                    st.markdown("##### 📋 업로드된 데이터 미리보기")
                    st.dataframe(upload_df.head(10), use_container_width=True, hide_index=True)
                    
                    # 분석 옵션
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        replace_existing = st.checkbox(
                            "기존 리스트 교체", 
                            value=False,
                            help="체크하면 기존 리스트를 완전히 교체합니다. 체크하지 않으면 추가됩니다."
                        )
                    
                    with col_b:
                        validate_symbols = st.checkbox(
                            "심볼 유효성 검증",
                            value=True,
                            help="업로드 전에 주식 심볼이 유효한지 확인합니다."
                        )
                    
                    # 업로드 적용 버튼
                    if st.button("🚀 업로드된 리스트로 분석 시작", type="primary"):
                        with st.spinner("업로드된 리스트를 처리하고 분석을 시작합니다..."):
                            
                            # 업로드된 데이터로 분석 실행
                            uploaded_symbols = upload_df['심볼'].tolist()
                            
                            if validate_symbols:
                                st.info("🔍 심볼 유효성 검증 중...")
                                # 여기에 심볼 유효성 검증 로직 추가 가능
                            
                            st.info(f"📊 {len(uploaded_symbols)}개 종목으로 분석을 시작합니다...")
                            
                            # 분석 실행
                            analysis_result = VOLATILITY_ANALYZER.detect_small_cap_stocks(
                                uploaded_symbols,
                                max_market_cap=5e11,  # 5000억원
                                min_volatility=20.0
                            )
                            
                            # 결과 표시
                            st.success(f"✅ 분석 완료! {len(analysis_result)}개 조건 충족 종목 발견")
                            display_small_cap_screening(analysis_result)
                            
            except Exception as e:
                st.error(f"파일 처리 중 오류 발생: {str(e)}")
    
    # 종목 관리 기능
    st.markdown("---")
    st.subheader("🛠️ 종목 관리")
    
    # 탭으로 구성
    mgmt_tab1, mgmt_tab2, mgmt_tab3, mgmt_tab4 = st.tabs(["➕ 수동 추가", "📊 대량 관리", "🔗 구글 시트 연동", "🗑️ 종목 삭제"])
    
    with mgmt_tab1:
        st.markdown("### 개별 종목 추가")
        col1, col2 = st.columns(2)
        with col1:
            new_market = st.selectbox("시장", ["korean_stocks", "us_stocks"], key="add_market")
            new_category = st.selectbox("카테고리", STOCK_LIST_MANAGER.get_categories(new_market), key="add_category")
        with col2:
            new_subcategory = st.selectbox("서브카테고리", STOCK_LIST_MANAGER.get_subcategories(new_market, new_category), key="add_subcategory")
            
        col3, col4 = st.columns(2)
        with col3:
            new_symbol = st.text_input("종목 코드", help="예: AAPL, 005930")
        with col4:
            new_name = st.text_input("종목명", help="예: Apple Inc, 삼성전자")
        
        if st.button("➕ 종목 추가", type="primary"):
            if new_symbol and new_name:
                STOCK_LIST_MANAGER.add_stock(new_market, new_category, new_subcategory, new_symbol, new_name)
                st.success(f"✅ {new_symbol} ({new_name}) 추가됨")
                st.rerun()
            else:
                st.error("종목 코드와 종목명을 모두 입력해주세요")
    
    with mgmt_tab2:
        st.markdown("### 📄 엑셀 파일 업로드")
        uploaded_file = st.file_uploader(
            "엑셀 파일 선택", 
            type=['xlsx', 'xls'],
            help="컬럼: market, category, subcategory, symbol, name"
        )
        
        if uploaded_file:
            try:
                df = pd.read_excel(uploaded_file)
                st.write("업로드된 데이터 미리보기:")
                st.dataframe(df.head())
                
                required_columns = ['market', 'category', 'subcategory', 'symbol', 'name']
                if all(col in df.columns for col in required_columns):
                    if st.button("📥 대량 업로드 실행"):
                        success_count = 0
                        for _, row in df.iterrows():
                            try:
                                STOCK_LIST_MANAGER.add_stock(
                                    row['market'], row['category'], 
                                    row['subcategory'], row['symbol'], row['name']
                                )
                                success_count += 1
                            except Exception as e:
                                st.error(f"오류 - {row['symbol']}: {e}")
                        
                        st.success(f"✅ {success_count}개 종목이 성공적으로 추가되었습니다!")
                        st.rerun()
                else:
                    st.error(f"필수 컬럼이 없습니다: {required_columns}")
            except Exception as e:
                st.error(f"파일 읽기 오류: {e}")
        
        # 템플릿 다운로드
        st.markdown("### 📋 템플릿 다운로드")
        template_df = pd.DataFrame({
            'market': ['korean_stocks', 'us_stocks'],
            'category': ['small_cap', 'small_cap'],
            'subcategory': ['IT_tech', 'biotech'],
            'symbol': ['123456', 'AAPL'],
            'name': ['예시회사', 'Apple Inc']
        })
        
        csv = template_df.to_csv(index=False)
        st.download_button(
            "📥 템플릿 다운로드",
            csv,
            "stock_template.csv",
            "text/csv"
        )
    
    with mgmt_tab3:
        st.markdown("### 🔗 구글 시트 연동")
        st.info("""
        **구글 시트 연동 방법:**
        1. 구글 시트를 공개로 설정하거나 API 키 설정
        2. 시트 URL 또는 시트 ID 입력
        3. 데이터 형식: A열(시장), B열(카테고리), C열(서브카테고리), D열(종목코드), E열(종목명)
        """)
        
        google_sheet_url = st.text_input(
            "구글 시트 URL", 
            placeholder="https://docs.google.com/spreadsheets/d/...",
            help="공개된 구글 시트 URL을 입력하세요"
        )
        
        if st.button("🔗 구글 시트에서 가져오기"):
            if google_sheet_url:
                try:
                    # 구글 시트 URL에서 CSV 형태로 데이터 가져오기
                    if "/edit" in google_sheet_url:
                        csv_url = google_sheet_url.replace("/edit#gid=", "/export?format=csv&gid=")
                        csv_url = csv_url.replace("/edit", "/export?format=csv")
                    else:
                        csv_url = google_sheet_url
                    
                    df = pd.read_csv(csv_url)
                    
                    # 컬럼명 표준화
                    df.columns = ['market', 'category', 'subcategory', 'symbol', 'name']
                    
                    st.write("구글 시트 데이터:")
                    st.dataframe(df)
                    
                    if st.button("📥 구글 시트 데이터 적용"):
                        success_count = 0
                        for _, row in df.iterrows():
                            try:
                                STOCK_LIST_MANAGER.add_stock(
                                    row['market'], row['category'], 
                                    row['subcategory'], row['symbol'], row['name']
                                )
                                success_count += 1
                            except Exception as e:
                                st.warning(f"건너뜀 - {row['symbol']}: {e}")
                        
                        st.success(f"✅ {success_count}개 종목이 구글 시트에서 가져와졌습니다!")
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"구글 시트 연동 오류: {e}")
                    st.info("URL이 공개되어 있는지 확인하고, CSV 내보내기가 가능한지 확인하세요.")
            else:
                st.error("구글 시트 URL을 입력해주세요")
    
    with mgmt_tab4:
        st.markdown("### 🗑️ 종목 삭제")
        
        # 삭제할 시장/카테고리 선택
        col1, col2 = st.columns(2)
        with col1:
            del_market = st.selectbox("삭제할 시장", ["korean_stocks", "us_stocks"], key="del_market")
            del_category = st.selectbox("삭제할 카테고리", STOCK_LIST_MANAGER.get_categories(del_market), key="del_category")
        with col2:
            del_subcategory = st.selectbox("삭제할 서브카테고리", STOCK_LIST_MANAGER.get_subcategories(del_market, del_category), key="del_subcategory")
        
        # 해당 카테고리의 종목들 표시
        stocks_in_category = STOCK_LIST_MANAGER.stock_lists[del_market][del_category][del_subcategory]
        
        if stocks_in_category:
            st.write(f"**{del_subcategory}** 카테고리의 종목들:")
            
            for symbol, name in stocks_in_category.items():
                col1, col2, col3 = st.columns([2, 4, 1])
                with col1:
                    st.write(f"**{symbol}**")
                with col2:
                    st.write(name)
                with col3:
                    if st.button("🗑️", key=f"del_{symbol}", help=f"{symbol} 삭제"):
                        if STOCK_LIST_MANAGER.remove_stock(del_market, del_category, del_subcategory, symbol):
                            st.success(f"✅ {symbol} 삭제됨")
                            st.rerun()
                        else:
                            st.error(f"❌ {symbol} 삭제 실패")
        else:
            st.info("해당 카테고리에 종목이 없습니다.")

def display_cache_management():
    """캐시 관리 UI"""
    st.subheader("🗂️ 캐시 관리")
    
    # 캐시 통계
    cache_stats = STOCK_CACHE.get_cache_stats()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("캐시 항목 수", cache_stats['total_entries'])
    with col2:
        st.metric("캐시 크기", f"{cache_stats['cache_size_mb']:.1f} MB")
    with col3:
        if st.button("🗑️ 오래된 캐시 정리"):
            cleared = STOCK_CACHE.clear_cache(older_than_hours=168)  # 7일
            st.success(f"{cleared}개 항목 정리됨")
            st.rerun()
    
    # 타입별 캐시 항목
    st.markdown("### 📊 캐시 항목별 현황")
    for cache_type, count in cache_stats['by_type'].items():
        st.markdown(f"**{cache_type}**: {count}개")
    
    # 캐시 상태 정보
    st.markdown("""
    ### ℹ️ 캐시 정책
    - **주식 정보**: 24시간 유지
    - **가격 데이터**: 6시간 유지  
    - **변동성 지수**: 1시간 유지
    - **자동 정리**: 7일 이상 된 항목 삭제
    
    💡 캐시를 사용하여 동일한 데이터 재조회를 방지하고 성능을 향상시킵니다.
    """)

def display_comprehensive_analysis(analysis_result):
    """종합 분석 결과 표시"""
    
    # 분석 요약
    st.subheader("📋 분석 요약")
    st.markdown(f"**분석 시각:** {analysis_result['timestamp']}")
    st.markdown(analysis_result['analysis_summary'])
    
    # 시장 심리
    st.subheader("🌡️ 현재 시장 심리")
    sentiment_cols = st.columns(len(analysis_result['market_sentiment']))
    for i, (key, value) in enumerate(analysis_result['market_sentiment'].items()):
        with sentiment_cols[i]:
            st.metric(key, value)
    
    # 변동성 지수 차트
    if analysis_result['volatility_indices']:
        st.subheader("📊 변동성 지수 추이")
        display_volatility_charts(analysis_result['volatility_indices'])
    
    # 상위 변동성 종목
    if analysis_result['top_volatile_stocks']:
        st.subheader("🔥 고변동성 소형주 TOP 10")
        display_volatile_stocks_table(analysis_result['top_volatile_stocks'])
        
        # 상위 5개 종목 상세 차트
        st.subheader("📈 상위 5개 종목 상세 분석")
        display_top_stocks_charts(analysis_result['top_volatile_stocks'][:5])

def display_volatility_indices(volatility_indices, market_sentiment):
    """변동성 지수 표시"""
    
    st.subheader("📊 변동성 지수 현황")
    
    # 시장 심리 요약
    sentiment_cols = st.columns(len(market_sentiment))
    for i, (key, value) in enumerate(market_sentiment.items()):
        with sentiment_cols[i]:
            st.metric(key, value)
    
    # 차트 표시
    display_volatility_charts(volatility_indices)

def display_small_cap_screening(small_caps):
    """소형주 스크리닝 결과 표시"""
    
    st.subheader(f"🔍 소형주 스크리닝 결과 ({len(small_caps)}개 종목)")
    
    if small_caps:
        display_volatile_stocks_table(small_caps)
        
        # 변동성 분포 차트
        st.subheader("📊 변동성 분포")
        volatilities = [stock.get('current_volatility', 0) for stock in small_caps]
        
        fig = px.histogram(
            x=volatilities,
            nbins=15,
            title="소형주 변동성 분포",
            labels={'x': '연간 변동성 (%)', 'y': '종목 수'}
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("조건에 맞는 소형주를 찾을 수 없습니다.")

def display_market_sentiment(market_sentiment, volatility_indices):
    """시장 심리 분석 표시"""
    
    st.subheader("🌡️ 시장 심리 분석")
    
    # 심리 지표 (개선된 색상 표시)
    sentiment_cols = st.columns(len(market_sentiment))
    for i, (key, value) in enumerate(market_sentiment.items()):
        with sentiment_cols[i]:
            # 현재 값 추출 및 상태 확인
            try:
                if key == 'VIX' and isinstance(volatility_indices, dict) and 'VIX' in volatility_indices:
                    vix_data = volatility_indices['VIX']
                    if not vix_data.empty and 'Close' in vix_data.columns:
                        current_vix = float(vix_data['Close'].iloc[-1])
                        status_emoji = get_vix_status(current_vix)
                        st.metric(
                            label=f"🌡️ {key}",
                            value=f"{current_vix:.1f}",
                            delta=status_emoji
                        )
                        if current_vix <= 20:
                            st.success(f"**{value}**")
                        elif current_vix <= 25:
                            st.warning(f"**{value}**")
                        elif current_vix <= 30:
                            st.error(f"**{value}**")
                        else:
                            st.error(f"🚨 **{value}**")
                    else:
                        st.info(f"**{key}**\n{value}")
                        
                elif 'KOSPI' in key and isinstance(volatility_indices, dict) and 'KOSPI_Volatility' in volatility_indices:
                    kospi_data = volatility_indices['KOSPI_Volatility']
                    if not kospi_data.empty and 'Close' in kospi_data.columns:
                        current_kospi = float(kospi_data['Close'].iloc[-1])
                        if not pd.isna(current_kospi):
                            status_emoji = get_volatility_status(current_kospi)
                            st.metric(
                                label=f"🇰🇷 {key}",
                                value=f"{current_kospi:.1f}%",
                                delta=status_emoji
                            )
                            if current_kospi <= 20:
                                st.success(f"**{value}**")
                            elif current_kospi <= 25:
                                st.warning(f"**{value}**")
                            elif current_kospi <= 30:
                                st.error(f"**{value}**")
                            else:
                                st.error(f"🚨 **{value}**")
                        else:
                            st.info(f"**{key}**\n{value}")
                    else:
                        st.info(f"**{key}**\n{value}")
                        
                elif 'KOSDAQ' in key and isinstance(volatility_indices, dict) and 'KOSDAQ_Volatility' in volatility_indices:
                    kosdaq_data = volatility_indices['KOSDAQ_Volatility']
                    if not kosdaq_data.empty and 'Close' in kosdaq_data.columns:
                        current_kosdaq = float(kosdaq_data['Close'].iloc[-1])
                        if not pd.isna(current_kosdaq):
                            status_emoji = get_volatility_status(current_kosdaq)
                            st.metric(
                                label=f"🇰🇷 {key}",
                                value=f"{current_kosdaq:.1f}%",
                                delta=status_emoji
                            )
                            if current_kosdaq <= 20:
                                st.success(f"**{value}**")
                            elif current_kosdaq <= 25:
                                st.warning(f"**{value}**")
                            elif current_kosdaq <= 30:
                                st.error(f"**{value}**")
                            else:
                                st.error(f"🚨 **{value}**")
                        else:
                            st.info(f"**{key}**\n{value}")
                    else:
                        st.info(f"**{key}**\n{value}")
                else:
                    # 기본 표시
                    if "극도공포" in value or "극고변동성" in value:
                        st.error(f"**{key}**\n{value}")
                    elif "공포" in value or "고변동성" in value:
                        st.warning(f"**{key}**\n{value}")
                    elif "불안" in value or "중변동성" in value:
                        st.info(f"**{key}**\n{value}")
                    else:
                        st.success(f"**{key}**\n{value}")
            except Exception as e:
                print(f"시장 심리 표시 오류 ({key}): {e}")
                # 기본 표시로 폴백
                if "극도공포" in value or "극고변동성" in value:
                    st.error(f"**{key}**\n{value}")
                elif "공포" in value or "고변동성" in value:
                    st.warning(f"**{key}**\n{value}")
                elif "불안" in value or "중변동성" in value:
                    st.info(f"**{key}**\n{value}")
                else:
                    st.success(f"**{key}**\n{value}")
    
    # 추천 투자 전략
    st.subheader("💡 추천 투자 전략")
    generate_investment_strategy(market_sentiment)

def display_volatility_charts(volatility_indices):
    """변동성 지수 차트 표시 (안전/위험 구간 색상 표시)"""
    
    charts_per_row = 2
    chart_pairs = list(volatility_indices.items())
    
    for i in range(0, len(chart_pairs), charts_per_row):
        cols = st.columns(charts_per_row)
        
        for j in range(charts_per_row):
            if i + j < len(chart_pairs):
                key, data = chart_pairs[i + j]
                
                with cols[j]:
                    if not data.empty and 'Close' in data.columns:
                        fig = go.Figure()
                        
                        # 데이터 라인 추가 (더 두껍고 눈에 잘 보이게)
                        fig.add_trace(go.Scatter(
                            x=data.index,
                            y=data['Close'],
                            mode='lines+markers',
                            name=key,
                            line=dict(width=4, color='#FF6B6B'),
                            marker=dict(size=6, color='#FF6B6B'),
                            hovertemplate='<b>%{fullData.name}</b><br>' +
                                        '날짜: %{x}<br>' +
                                        '값: %{y:.2f}<br>' +
                                        '<extra></extra>'
                        ))
                        
                        # 안전/위험 구간 색상 표시
                        try:
                            y_min = float(data['Close'].min())
                            y_max = float(data['Close'].max())
                        except Exception as e:
                            print(f"Y축 범위 계산 오류: {e}")
                            y_min = 0
                            y_max = 100
                        
                        # VIX 구간 설정
                        if key == 'VIX':
                            # 안전 구간 (12-20): 초록색
                            fig.add_hrect(y0=12, y1=20, 
                                        fillcolor="green", opacity=0.2,
                                        annotation_text="안전 구간 (12-20)", 
                                        annotation_position="top left")
                            
                            # 주의 구간 (20-25): 노란색
                            fig.add_hrect(y0=20, y1=25, 
                                        fillcolor="yellow", opacity=0.2,
                                        annotation_text="주의 구간 (20-25)", 
                                        annotation_position="top left")
                            
                            # 위험 구간 (25-30): 주황색
                            fig.add_hrect(y0=25, y1=30, 
                                        fillcolor="orange", opacity=0.2,
                                        annotation_text="위험 구간 (25-30)", 
                                        annotation_position="top left")
                            
                            # 극위험 구간 (30+): 빨간색
                            fig.add_hrect(y0=30, y1=max(50, float(y_max)), 
                                        fillcolor="red", opacity=0.2,
                                        annotation_text="극위험 구간 (30+)", 
                                        annotation_position="top left")
                            
                            current_value = float(data['Close'].iloc[-1])
                            status = get_vix_status(current_value)
                            
                        # SKEW 구간 설정  
                        elif key == 'SKEW':
                            # 안전 구간 (100-120): 초록색
                            fig.add_hrect(y0=100, y1=120, 
                                        fillcolor="green", opacity=0.2,
                                        annotation_text="안전 구간 (100-120)", 
                                        annotation_position="top left")
                            
                            # 주의 구간 (120-130): 노란색
                            fig.add_hrect(y0=120, y1=130, 
                                        fillcolor="yellow", opacity=0.2,
                                        annotation_text="주의 구간 (120-130)", 
                                        annotation_position="top left")
                            
                            # 위험 구간 (130-140): 주황색
                            fig.add_hrect(y0=130, y1=140, 
                                        fillcolor="orange", opacity=0.2,
                                        annotation_text="위험 구간 (130-140)", 
                                        annotation_position="top left")
                            
                            # 극위험 구간 (140+): 빨간색
                            fig.add_hrect(y0=140, y1=max(160, float(y_max)), 
                                        fillcolor="red", opacity=0.2,
                                        annotation_text="극위험 구간 (140+)", 
                                        annotation_position="top left")
                            
                            current_value = float(data['Close'].iloc[-1])
                            status = get_skew_status(current_value)
                            
                        # 변동성 구간 설정
                        elif 'Volatility' in key:
                            # 안전 구간 (10-20%): 초록색
                            fig.add_hrect(y0=10, y1=20, 
                                        fillcolor="green", opacity=0.2,
                                        annotation_text="안전 구간 (10-20%)", 
                                        annotation_position="top left")
                            
                            # 주의 구간 (20-25%): 노란색
                            fig.add_hrect(y0=20, y1=25, 
                                        fillcolor="yellow", opacity=0.2,
                                        annotation_text="주의 구간 (20-25%)", 
                                        annotation_position="top left")
                            
                            # 위험 구간 (25-30%): 주황색
                            fig.add_hrect(y0=25, y1=30, 
                                        fillcolor="orange", opacity=0.2,
                                        annotation_text="위험 구간 (25-30%)", 
                                        annotation_position="top left")
                            
                            # 극위험 구간 (30%+): 빨간색
                            fig.add_hrect(y0=30, y1=max(50, float(y_max)), 
                                        fillcolor="red", opacity=0.2,
                                        annotation_text="극위험 구간 (30%+)", 
                                        annotation_position="top left")
                            
                            current_value = float(data['Close'].iloc[-1])
                            status = get_volatility_status(current_value)
                        else:
                            status = ""
                        
                        fig.update_layout(
                            title=f"{key} 추이 {status}",
                            xaxis_title="날짜",
                            yaxis_title="값",
                            height=400,
                            showlegend=True,
                            template="plotly_white",
                            hovermode='x unified'
                        )
                        
                        # Y축 포맷 개선 (소수점 둘째자리까지)
                        fig.update_yaxes(
                            tickformat=".2f",
                            gridcolor="rgba(128,128,128,0.3)",
                            gridwidth=1
                        )
                        
                        # X축 포맷 개선
                        fig.update_xaxes(
                            gridcolor="rgba(128,128,128,0.3)",
                            gridwidth=1
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)

def get_vix_status(value: float) -> str:
    """VIX 값에 따른 상태 표시"""
    if value <= 20:
        return "🟢 (안전)"
    elif value <= 25:
        return "🟡 (주의)"
    elif value <= 30:
        return "🟠 (위험)"
    else:
        return "🔴 (극위험)"

def get_skew_status(value: float) -> str:
    """SKEW 값에 따른 상태 표시"""
    if value <= 120:
        return "🟢 (안전)"
    elif value <= 130:
        return "🟡 (주의)"
    elif value <= 140:
        return "🟠 (위험)"
    else:
        return "🔴 (극위험)"

def get_volatility_status(value: float) -> str:
    """변동성 값에 따른 상태 표시"""
    if value <= 20:
        return "🟢 (안전)"
    elif value <= 25:
        return "🟡 (주의)"
    elif value <= 30:
        return "🟠 (위험)"
    else:
        return "🔴 (극위험)"

def display_volatile_stocks_table(stocks):
    """변동성 높은 종목 테이블 표시 (개선된 정보)"""
    
    if not stocks:
        st.warning("표시할 종목이 없습니다.")
        return
    
    # 데이터프레임 생성
    df_data = []
    for stock in stocks:
        df_data.append({
            '종목코드': stock.get('symbol', 'N/A'),
            '종목명': stock.get('name', 'N/A'),
            '카테고리': f"{stock.get('category', 'N/A')} > {stock.get('subcategory', 'N/A')}",
            '시가총액등급': stock.get('market_cap_tier', 'N/A'),
            '시가총액': f"{stock.get('market_cap', 0)/1e8:.0f}억원" if stock.get('market_cap') else 'N/A',
            '현재가격': f"${stock.get('price', 0):,.0f}" if stock.get('price') else 'N/A',
            '변동성': f"{stock.get('current_volatility', 0):.1f}%",
            '변동성등급': stock.get('volatility_rank', 'N/A'),
            'RSI': f"{stock.get('RSI', 0):.1f}" if stock.get('RSI') else 'N/A',
            '5일수익률': f"{stock.get('price_change_5d', 0):+.1f}%" if stock.get('price_change_5d') else 'N/A',
            '거래량비율': f"{stock.get('volume_ratio', 1):.2f}x",
            '분석일시': stock.get('analysis_date', 'N/A')
        })
    
    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True)
    
    # 요약 통계
    st.markdown("### 📊 분석 요약")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        try:
            volatilities = [float(s.get('current_volatility', 0)) for s in stocks if isinstance(s.get('current_volatility', 0), (int, float)) and not pd.isna(s.get('current_volatility', 0))]
            avg_volatility = sum(volatilities) / len(volatilities) if volatilities else 0
            st.metric("평균 변동성", f"{avg_volatility:.1f}%")
        except Exception as e:
            print(f"평균 변동성 계산 오류: {e}")
            st.metric("평균 변동성", "N/A")
    
    with col2:
        try:
            high_vol_count = sum(1 for s in stocks if isinstance(s.get('current_volatility', 0), (int, float)) and s.get('current_volatility', 0) >= 50)
            st.metric("극고변동성 종목", f"{high_vol_count}개")
        except Exception as e:
            print(f"극고변동성 종목 계산 오류: {e}")
            st.metric("극고변동성 종목", "N/A")
    
    with col3:
        small_cap_count = sum(1 for s in stocks if s.get('market_cap_tier') in ['소형주', '소소형주', '극소형주'])
        st.metric("소형주 이하", f"{small_cap_count}개")
    
    with col4:
        high_rsi_count = sum(1 for s in stocks if s.get('RSI', 0) >= 70)
        st.metric("과매수(RSI≥70)", f"{high_rsi_count}개")

def display_top_stocks_charts(top_stocks):
    """상위 종목들의 상세 차트 표시"""
    
    for i, stock in enumerate(top_stocks):
        symbol = stock.get('symbol')
        name = stock.get('name', 'Unknown')
        
        if symbol:
            try:
                # 최근 3개월 데이터
                ticker_symbol = f"{symbol}.KS" if len(symbol) == 6 else symbol
                data = yf.download(ticker_symbol, period="3mo", progress=False)
                
                if not data.empty:
                    st.markdown(f"**{i+1}. {symbol} - {name}**")
                    
                    fig = go.Figure()
                    
                    # 캔들스틱 차트
                    fig.add_trace(go.Candlestick(
                        x=data.index,
                        open=data['Open'],
                        high=data['High'],
                        low=data['Low'],
                        close=data['Close'],
                        name=symbol
                    ))
                    
                    # 볼린저 밴드 추가
                    sma_20 = data['Close'].rolling(window=20).mean()
                    std_20 = data['Close'].rolling(window=20).std()
                    bb_upper = sma_20 + (std_20 * 2)
                    bb_lower = sma_20 - (std_20 * 2)
                    
                    fig.add_trace(go.Scatter(x=data.index, y=bb_upper, line=dict(color='red', dash='dash'), name='BB상단'))
                    fig.add_trace(go.Scatter(x=data.index, y=bb_lower, line=dict(color='red', dash='dash'), name='BB하단'))
                    
                    fig.update_layout(
                        title=f"{symbol} - {name} (최근 3개월)",
                        yaxis_title="가격",
                        height=400
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
            except Exception as e:
                st.error(f"{symbol} 차트 생성 실패: {e}")

def generate_investment_strategy(market_sentiment):
    """시장 심리에 따른 투자 전략 생성 (수치 기반)"""
    
    strategies = []
    risk_level = "중간"
    
    # VIX 기반 전략 (구체적 수치 반영)
    if 'VIX' in market_sentiment:
        vix_sentiment = market_sentiment['VIX']
        if "극도공포" in vix_sentiment:  # VIX 30+
            strategies.append("🚨 **극도 위험 (VIX 30+)**: 현금 비중 80%+, 모든 레버리지 포지션 정리")
            strategies.append("💰 **방어 전략**: 국채, 금, 달러 등 안전자산 위주")
            risk_level = "극고위험"
        elif "공포" in vix_sentiment:  # VIX 25-30
            strategies.append("⚠️ **고위험 (VIX 25-30)**: 포지션 50% 축소, 옵션 매도 중단")
            strategies.append("🛡️ **방어적 투자**: 배당주, 우량 대형주 위주")
            risk_level = "고위험"
        elif "불안" in vix_sentiment:  # VIX 20-25
            strategies.append("📊 **선별적 투자 (VIX 20-25)**: 우량 소형주 위주, 소량 분할 매수")
            strategies.append("⚖️ **균형 전략**: 현금 30%, 주식 70% 비중 유지")
            risk_level = "중위험"
        else:  # VIX 12-20
            strategies.append("✅ **적극적 투자 (VIX 12-20)**: 성장주, 테마주 발굴 적기")
            strategies.append("🚀 **공격적 전략**: 소형주, 신기술 관련주 집중 투자")
            risk_level = "저위험"
    
    # KOSDAQ 변동성 기반 전략
    if 'KOSDAQ' in market_sentiment:
        kosdaq_sentiment = market_sentiment['KOSDAQ']
        if "극고변동성" in kosdaq_sentiment:  # 30%+
            strategies.append("⚡ **초단타 전략 (변동성 30%+)**: 일일 매매, 2% 손절 원칙")
            strategies.append("📉 **리스크 관리**: 포지션 크기 평소의 1/3로 축소")
        elif "고변동성" in kosdaq_sentiment:  # 20-30%
            strategies.append("📈 **테마주 활성 (변동성 20-30%)**: 강한 테마 위주 단기 투자")
            strategies.append("🎯 **스윙 트레이딩**: 3-5일 보유, 5% 손절선 설정")
        else:  # 10-20%
            strategies.append("🎯 **중장기 투자 (변동성 10-20%)**: 펀더멘털 우수 소형주 발굴")
            strategies.append("📊 **포트폴리오 구성**: 성장주 70%, 가치주 30% 분산")
    
    # 종합 리스크 레벨 표시
    st.markdown("### 🎯 현재 시장 위험도")
    if risk_level == "극고위험":
        st.error(f"🔴 **{risk_level}** - 모든 위험 자산 회피 권장")
    elif risk_level == "고위험":
        st.warning(f"🟠 **{risk_level}** - 방어적 포지션 유지")
    elif risk_level == "중위험":
        st.info(f"🟡 **{risk_level}** - 선별적 투자 및 리스크 관리")
    else:
        st.success(f"🟢 **{risk_level}** - 적극적 투자 기회")
    
    # 전략 표시
    st.markdown("### 📋 추천 투자 전략")
    for i, strategy in enumerate(strategies, 1):
        st.markdown(f"{i}. {strategy}")
    
    # 구체적 행동 지침
    st.markdown("### 🎲 구체적 행동 지침")
    
    if risk_level == "극고위험":
        st.markdown("""
        - 💵 **현금 비중**: 80% 이상 유지
        - 🚫 **금지 행동**: 신용매수, 옵션 매수, 레버리지 상품
        - 🛡️ **안전 자산**: 국채 ETF, 금 ETF 고려
        - ⏰ **재진입 시점**: VIX 25 이하로 하락 시
        """)
    elif risk_level == "고위험":
        st.markdown("""
        - 💵 **현금 비중**: 50-60% 유지
        - ⚠️ **주의 행동**: 소량 분할 매수, 손절선 엄격 준수
        - 🏢 **추천 종목**: 대형주, 배당주, 방어주
        - ⏰ **관찰 포인트**: VIX 20 이하 진입 여부
        """)
    elif risk_level == "중위험":
        st.markdown("""
        - 💵 **현금 비중**: 30-40% 유지
        - 📊 **투자 방식**: 분할 매수, 단계적 진입
        - 🎯 **추천 종목**: 우량 소형주, 테마주 선별
        - ⏰ **전환 시점**: VIX 방향성 확인 후 비중 조절
        """)
    else:
        st.markdown("""
        - 💵 **현금 비중**: 10-20% 유지 (기회 대기)
        - 🚀 **투자 방식**: 적극적 매수, 성장주 발굴
        - 💎 **추천 종목**: 소형주, 신기술, 테마주
        - ⏰ **주의 시점**: VIX 20 돌파 시 포지션 조절
        """)
    
    # 추가 주의사항
    st.markdown("---")
    st.warning("""
    **⚠️ 리스크 관리 원칙**
    
    **1. 손절 원칙**
    - 안전 구간: -10% 손절
    - 주의 구간: -7% 손절  
    - 위험 구간: -5% 손절
    - 극위험 구간: -3% 손절
    
    **2. 포지션 관리**
    - 개별 종목 최대 5% 비중
    - 동일 섹터 최대 20% 비중
    - 소형주 전체 최대 40% 비중
    
    **3. 변동성 모니터링**
    - VIX 20 돌파 시 즉시 점검
    - 개별 종목 변동성 30% 초과 시 비중 축소
    - 시장 심리 변화 시 전략 재검토
    """)

def ticker_management_page():
    """티커 관리 페이지"""
    st.title("🔧 티커 관리 시스템")
    st.markdown("**주식 티커 추가 • 수정 • 삭제** | 엑셀 파일 관리 및 Google Sheets 연동")
    st.markdown("---")
    
    # 티커 관리 UI 표시
    ticker_management_ui()

def main():
    """메인 함수: 페이지 네비게이션 및 라우팅"""
    
    # 앱 시작 시 영구 저장소 초기화
    initialize_persistent_storage()
    
    # 사이드바에 페이지 선택 추가
    st.sidebar.title("📊 통합 금융 분석기")
    
    # 페이지 선택
    page = st.sidebar.selectbox(
        "분석 도구 선택:",
        ["📈 주식 분석", "📊 매크로 경제 분석", "🎯 잡주 분석", "🔧 티커 관리"],
        help="원하는 분석 도구를 선택하세요"
    )
    
    # 선택된 페이지에 따라 함수 실행
    if page == "📈 주식 분석":
        stock_analysis_page()
    elif page == "📊 매크로 경제 분석":
        macro_analysis_page()
    elif page == "🎯 잡주 분석":
        volatility_analysis_page()
    elif page == "🔧 티커 관리":
        ticker_management_page()

if __name__ == "__main__":
    main()
