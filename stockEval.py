"""
해외 곡물 관련 주식 10년치 주가 분석 프로그램
곡물 관련 대표 주식들의 주가 추이를 분석하고 시각화합니다.
"""

import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 한글 폰트 설정 (Windows)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 곡물 관련 주식 티커 심볼 정의
GRAIN_STOCKS = {
    'ADM': '아처 대니얼스 미들랜드',
    'BG': '번지',
    'DE': '디어앤컴퍼니', 
    'CNHI': 'CNH 인더스트리얼',
    'GIS': '제너럴 밀스',
    'K': '켈로그',
    'TSN': '타이슨 푸드',
    'CTVA': '코르테바'  # 코르테바의 정확한 티커는 CTVA입니다
}

def fetch_stock_data(tickers, period='10y'):
    """
    주식 데이터를 가져오는 함수
    
    Args:
        tickers (list): 주식 티커 심볼 리스트
        period (str): 데이터 기간 ('10y' = 10년)
    
    Returns:
        dict: 각 티커별 주가 데이터
    """
    stock_data = {}
    
    print("주가 데이터 수집 중...")
    for ticker in tickers:
        try:
            print(f"  - {ticker} ({GRAIN_STOCKS[ticker]}) 데이터 수집 중...")
            stock = yf.Ticker(ticker)
            data = stock.history(period=period)
            
            if not data.empty:
                stock_data[ticker] = data
                print(f"    ✓ {ticker}: {len(data)} 일간 데이터 수집 완료")
            else:
                print(f"    ✗ {ticker}: 데이터 없음")
                
        except Exception as e:
            print(f"    ✗ {ticker} 데이터 수집 실패: {str(e)}")
    
    return stock_data

def normalize_prices(stock_data):
    """
    주가를 정규화하여 비교 가능하게 만드는 함수
    (시작점을 100으로 설정하여 상대적 변화율 표시)
    
    Args:
        stock_data (dict): 원본 주가 데이터
    
    Returns:
        pandas.DataFrame: 정규화된 주가 데이터
    """
    normalized_data = pd.DataFrame()
    
    for ticker, data in stock_data.items():
        if not data.empty:
            # 종가 기준으로 정규화 (첫 번째 값을 100으로 설정)
            closing_prices = data['Close']
            normalized_prices = (closing_prices / closing_prices.iloc[0]) * 100
            normalized_data[ticker] = normalized_prices
    
    return normalized_data

def create_price_chart(stock_data):
    """
    개별 주가 차트 생성
    """
    fig, axes = plt.subplots(2, 4, figsize=(20, 12))
    fig.suptitle('곡물 관련 주식 10년 주가 추이 (개별 차트)', fontsize=16, fontweight='bold')
    
    axes = axes.flatten()
    
    for i, (ticker, data) in enumerate(stock_data.items()):
        if i < len(axes) and not data.empty:
            ax = axes[i]
            ax.plot(data.index, data['Close'], linewidth=1.5, color='blue')
            ax.set_title(f'{ticker} - {GRAIN_STOCKS[ticker]}', fontweight='bold')
            ax.set_ylabel('주가 (USD)')
            ax.grid(True, alpha=0.3)
            ax.tick_params(axis='x', rotation=45)
    
    # 빈 subplot 숨기기
    for i in range(len(stock_data), len(axes)):
        axes[i].set_visible(False)
    
    plt.tight_layout()
    plt.show()

def create_normalized_comparison_chart(normalized_data):
    """
    정규화된 주가 비교 차트 생성
    """
    plt.figure(figsize=(15, 10))
    
    # 색상 팔레트 설정
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F']
    
    for i, (ticker, prices) in enumerate(normalized_data.items()):
        plt.plot(prices.index, prices, 
                label=f'{ticker} - {GRAIN_STOCKS[ticker]}', 
                linewidth=2, 
                color=colors[i % len(colors)])
    
    plt.title('곡물 관련 주식 10년 수익률 비교 (정규화된 주가)', fontsize=16, fontweight='bold')
    plt.xlabel('날짜', fontsize=12)
    plt.ylabel('정규화된 주가 (시작점 = 100)', fontsize=12)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    
    # 수평선 추가 (시작점 표시)
    plt.axhline(y=100, color='red', linestyle='--', alpha=0.5, label='시작점 (100)')
    
    plt.tight_layout()
    plt.show()

def calculate_performance_metrics(normalized_data):
    """
    성과 지표 계산 및 출력
    """
    print("\n" + "="*60)
    print("주식별 성과 분석 (10년 기준)")
    print("="*60)
    
    performance_summary = []
    
    for ticker in normalized_data.columns:
        prices = normalized_data[ticker].dropna()
        if len(prices) > 0:
            start_price = prices.iloc[0]
            end_price = prices.iloc[-1]
            total_return = ((end_price - start_price) / start_price) * 100
            
            # 연간 수익률 계산
            years = len(prices) / 252  # 연간 거래일 약 252일
            annual_return = ((end_price / start_price) ** (1/years) - 1) * 100
            
            # 변동성 계산 (일간 수익률의 표준편차)
            daily_returns = prices.pct_change().dropna()
            volatility = daily_returns.std() * np.sqrt(252) * 100  # 연간 변동성
            
            performance_summary.append({
                '티커': ticker,
                '회사명': GRAIN_STOCKS[ticker],
                '총 수익률(%)': f"{total_return:.1f}%",
                '연간 수익률(%)': f"{annual_return:.1f}%",
                '연간 변동성(%)': f"{volatility:.1f}%"
            })
            
            print(f"{ticker:4} ({GRAIN_STOCKS[ticker]:<15}): 총 수익률 {total_return:6.1f}% | 연 수익률 {annual_return:5.1f}% | 변동성 {volatility:5.1f}%")
    
    return performance_summary

def create_performance_bar_chart(normalized_data):
    """
    성과 비교 막대그래프 생성
    """
    returns = []
    labels = []
    
    for ticker in normalized_data.columns:
        prices = normalized_data[ticker].dropna()
        if len(prices) > 0:
            total_return = ((prices.iloc[-1] - prices.iloc[0]) / prices.iloc[0]) * 100
            returns.append(total_return)
            labels.append(f'{ticker}\n{GRAIN_STOCKS[ticker]}')
    
    plt.figure(figsize=(12, 8))
    colors = ['green' if r > 0 else 'red' for r in returns]
    bars = plt.bar(range(len(returns)), returns, color=colors, alpha=0.7)
    
    # 막대 위에 수치 표시
    for i, (bar, ret) in enumerate(zip(bars, returns)):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + (5 if ret > 0 else -15), 
                f'{ret:.1f}%', ha='center', va='bottom' if ret > 0 else 'top', fontweight='bold')
    
    plt.title('곡물 관련 주식 10년 총 수익률 비교', fontsize=16, fontweight='bold')
    plt.ylabel('총 수익률 (%)', fontsize=12)
    plt.xticks(range(len(labels)), labels, rotation=45, ha='right')
    plt.grid(True, alpha=0.3, axis='y')
    plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    
    plt.tight_layout()
    plt.show()

def main():
    """
    메인 실행 함수
    """
    print("곡물 관련 주식 분석 프로그램을 시작합니다...")
    print(f"분석 대상: {list(GRAIN_STOCKS.keys())}")
    
    # 1. 주가 데이터 수집
    tickers = list(GRAIN_STOCKS.keys())
    stock_data = fetch_stock_data(tickers, period='10y')
    
    if not stock_data:
        print("수집된 주가 데이터가 없습니다.")
        return
    
    print(f"\n총 {len(stock_data)}개 주식의 데이터를 성공적으로 수집했습니다.")
    
    # 2. 데이터 정규화
    normalized_data = normalize_prices(stock_data)
    
    # 3. 차트 생성
    print("\n차트를 생성하고 있습니다...")
    
    # 개별 주가 차트
    create_price_chart(stock_data)
    
    # 정규화된 비교 차트
    create_normalized_comparison_chart(normalized_data)
    
    # 성과 비교 막대그래프
    create_performance_bar_chart(normalized_data)
    
    # 4. 성과 지표 계산
    performance_summary = calculate_performance_metrics(normalized_data)
    
    print("\n분석이 완료되었습니다!")
    print("생성된 차트들을 확인해보세요.")

if __name__ == "__main__":
    main()