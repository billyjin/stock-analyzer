"""
잡주(소형주/테마주) 변동성 분석 모듈

주요 기능:
1. VIX, SKEW 등 변동성 지수 수집
2. 한국 시장 변동성 지표 계산
3. 소형주 탐지 및 분석
4. 변동성 기반 잡주 스크리닝
"""

import yfinance as yf
import pandas as pd
import numpy as np
import warnings
from datetime import datetime, timedelta
import requests
from typing import Dict, List, Tuple, Optional
import time
from stock_cache import STOCK_CACHE
from stock_lists import STOCK_LIST_MANAGER

warnings.filterwarnings('ignore')

class VolatilityAnalyzer:
    """변동성 분석기"""
    
    def __init__(self):
        self.vix_symbol = "^VIX"
        self.skew_symbol = "^SKEW"  # SKEW가 지원되지 않을 수 있음
        self.kospi_symbol = "^KS11"
        self.kosdaq_symbol = "^KQ11"
        
        # 대안 심볼들
        self.vix_alternatives = ["^VIX", "VIX"]
        self.available_symbols = []
        
        # 한국 섹터 분류
        self.korean_sectors = {
            "IT/테크": ["005930", "000660", "035420", "035720", "051910"],  # 삼성전자, SK하이닉스, NAVER, 카카오, LG화학
            "바이오/제약": ["207940", "068270", "326030", "196170", "214450"],  # 삼성바이오, 셀트리온, SK바이오팜, 알테오젠, 파마리서치
            "게임": ["036570", "251270", "112040", "259960", "194480"],  # 엔씨소프트, 넷마블, 위메이드, 크래프톤, 데브시스터즈
            "자동차": ["005380", "000270", "012330", "161390", "018880"],  # 현대차, 기아, 현대모비스, 한국타이어, 한온시스템
            "화학": ["051910", "009830", "011170", "010950", "006400"],  # LG화학, 한화솔루션, 롯데케미칼, S-Oil, 삼성SDI
            "금융": ["055550", "086790", "316140", "138930", "024110"],  # 신한지주, 하나금융지주, 우리금융지주, BNK금융지주, 기업은행
            "건설": ["000720", "028050", "047040", "375500", "001040"],  # 현대건설, 삼성물산, 대우건설, DL이앤씨, CJ
            "유통/소비재": ["097950", "271560", "161890", "012750", "282330"],  # CJ제일제당, 오리온, 한국콜마, 에스텍, BGF리테일
            "에너지": ["034730", "018880", "267250", "010950", "009540"],  # SK에너지, 한온시스템, HD현대중공업, S-Oil, HD한국조선해양
            "소형주/테마": []  # 동적으로 추가
        }
        
    def get_volatility_indices(self, period: str = "1mo") -> Dict[str, pd.DataFrame]:
        """변동성 지수들 수집 (캐싱 지원) - 히스토리 데이터 개선"""
        
        # 캐시에서 먼저 확인
        cached_indices = STOCK_CACHE.get_volatility_indices(period, max_age_hours=1)
        if cached_indices:
            print("📋 캐시된 변동성 지수 데이터 사용")
            return cached_indices
        
        print("🔄 새로운 변동성 지수 데이터 수집 중...")
        indices = {}
        
        try:
            # VIX (공포지수) - 더 견고한 데이터 수집
            print("📊 VIX 데이터 수집 중...")
            vix_success = False
            for vix_sym in self.vix_alternatives:
                try:
                    print(f"🔍 {vix_sym} 심볼로 VIX 데이터 시도...")
                    vix = yf.download(vix_sym, period=period, progress=False, interval="1d")
                    if not vix.empty and len(vix) > 0:
                        # 멀티레벨 컬럼 구조 처리
                        if len(vix.columns.levels) > 1:
                            # 멀티레벨 컬럼인 경우 (('Close', '^VIX'))
                            vix.columns = vix.columns.droplevel(1)
                        
                        print(f"✅ VIX 데이터 수집 완료: {len(vix)}개 데이터 포인트")
                        start_date = vix.index[0].strftime('%Y-%m-%d')
                        end_date = vix.index[-1].strftime('%Y-%m-%d')
                        current_value = float(vix['Close'].iloc[-1])
                        print(f"📅 VIX 기간: {start_date} ~ {end_date}")
                        print(f"🔢 VIX 현재값: {current_value:.2f}")
                        indices['VIX'] = vix
                        vix_success = True
                        break
                except Exception as e:
                    print(f"❌ {vix_sym} 실패: {e}")
                    continue
            
            if not vix_success:
                print("❌ 모든 VIX 심볼에서 데이터 수집 실패")
                
            # SKEW Index (테일 리스크) - SKEW는 야후 파이낸스에서 제공하지 않을 수 있음
            print("📊 SKEW 데이터 수집 중...")
            try:
                skew = yf.download(self.skew_symbol, period=period, progress=False, interval="1d")
                if not skew.empty and len(skew) > 0:
                    # 멀티레벨 컬럼 구조 처리
                    if len(skew.columns.levels) > 1:
                        skew.columns = skew.columns.droplevel(1)
                    
                    print(f"✅ SKEW 데이터 수집 완료: {len(skew)}개 데이터 포인트")
                    start_date = skew.index[0].strftime('%Y-%m-%d')
                    end_date = skew.index[-1].strftime('%Y-%m-%d')
                    current_value = float(skew['Close'].iloc[-1])
                    print(f"📅 SKEW 기간: {start_date} ~ {end_date}")
                    print(f"🔢 SKEW 현재값: {current_value:.2f}")
                    indices['SKEW'] = skew
                else:
                    print("⚠️ SKEW 데이터가 비어있음 - 야후 파이낸스에서 지원하지 않을 수 있습니다")
                    # SKEW 대신 VIX 기반으로 계산된 SKEW 값 생성
                    if 'VIX' in indices:
                        print("🔄 VIX 기반으로 SKEW 추정값 생성...")
                        # 일반적으로 SKEW는 100-150 범위, VIX와 상관관계 있음
                        vix_data = indices['VIX'].copy()
                        # 간단한 추정: SKEW ≈ 100 + (VIX - 15) * 2
                        estimated_skew = vix_data['Close'].apply(lambda x: max(100, min(150, 100 + (x - 15) * 2)))
                        skew_df = pd.DataFrame(index=vix_data.index)
                        skew_df['Close'] = estimated_skew
                        skew_df['Open'] = estimated_skew
                        skew_df['High'] = estimated_skew * 1.01
                        skew_df['Low'] = estimated_skew * 0.99
                        skew_df['Volume'] = 0
                        indices['SKEW'] = skew_df
                        print(f"✅ SKEW 추정값 생성 완료: {len(skew_df)}개 데이터 포인트")
                        print(f"🔢 SKEW 추정 현재값: {float(skew_df['Close'].iloc[-1]):.2f}")
            except Exception as e:
                print(f"❌ SKEW 데이터 수집 실패: {e}")
                print("🔄 VIX 기반 SKEW 추정값 생성 시도...")
                if 'VIX' in indices:
                    vix_data = indices['VIX'].copy()
                    estimated_skew = vix_data['Close'].apply(lambda x: max(100, min(150, 100 + (x - 15) * 2)))
                    skew_df = pd.DataFrame(index=vix_data.index)
                    skew_df['Close'] = estimated_skew
                    skew_df['Open'] = estimated_skew
                    skew_df['High'] = estimated_skew * 1.01
                    skew_df['Low'] = estimated_skew * 0.99
                    skew_df['Volume'] = 0
                    indices['SKEW'] = skew_df
                    print(f"✅ SKEW 추정값 생성 완료: {len(skew_df)}개 데이터 포인트")
                
            # KOSPI 변동성 계산
            print("📊 KOSPI 데이터 수집 중...")
            kospi = yf.download(self.kospi_symbol, period=period, progress=False)
            if not kospi.empty:
                # 멀티레벨 컬럼 구조 처리
                if len(kospi.columns.levels) > 1:
                    kospi.columns = kospi.columns.droplevel(1)
                
                kospi_volatility = self.calculate_volatility(kospi)
                if not kospi_volatility.empty:
                    indices['KOSPI_Volatility'] = kospi_volatility
                    print(f"✅ KOSPI 변동성 계산 완료")
                
            # KOSDAQ 변동성 계산
            print("📊 KOSDAQ 데이터 수집 중...")
            kosdaq = yf.download(self.kosdaq_symbol, period=period, progress=False)
            if not kosdaq.empty:
                # 멀티레벨 컬럼 구조 처리
                if len(kosdaq.columns.levels) > 1:
                    kosdaq.columns = kosdaq.columns.droplevel(1)
                
                kosdaq_volatility = self.calculate_volatility(kosdaq)
                if not kosdaq_volatility.empty:
                    indices['KOSDAQ_Volatility'] = kosdaq_volatility
                    print(f"✅ KOSDAQ 변동성 계산 완료")
            
            # 캐시에 저장
            if indices:
                STOCK_CACHE.save_volatility_indices(period, indices)
                print("💾 변동성 지수 데이터 캐시에 저장됨")
                
        except Exception as e:
            import traceback
            print(f"❌ 변동성 지수 수집 오류: {e}")
            print("🔧 상세 오류 정보:")
            print(traceback.format_exc())
            
        return indices
        
    def calculate_volatility(self, price_data: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """가격 데이터에서 변동성 계산"""
        try:
            if price_data.empty or 'Close' not in price_data.columns:
                return pd.DataFrame()
                
            # 일일 수익률 계산
            returns = price_data['Close'].pct_change().dropna()
            
            if len(returns) < window:
                return pd.DataFrame()
            
            # 롤링 변동성 계산 (연율화)
            volatility = returns.rolling(window=window).std() * np.sqrt(252) * 100
            
            # Series를 DataFrame으로 안전하게 변환
            vol_df = pd.DataFrame(index=volatility.index)
            vol_df['Close'] = volatility.values  # .values로 1차원 배열 추출
            
            return vol_df
            
        except Exception as e:
            print(f"변동성 계산 오류: {e}")
            return pd.DataFrame()
        
    def get_stock_info(self, symbol: str) -> Dict:
        """주식 정보 수집 (한국/미국 주식 지원, 캐싱 지원)"""
        
        # 캐시에서 먼저 확인
        cached_info = STOCK_CACHE.get_stock_info(symbol, max_age_hours=24)
        if cached_info:
            return cached_info
        
        try:
            # 티커 심볼 결정
            if len(symbol) == 6 and symbol.isdigit():
                # 한국 주식 (6자리 숫자)
                ticker_symbol = f"{symbol}.KS"
            elif any(char.isalpha() for char in symbol):
                # 미국 주식 (알파벳 포함)
                ticker_symbol = symbol
            else:
                # 기타 경우
                ticker_symbol = symbol
                
            stock = yf.Ticker(ticker_symbol)
            info = stock.info
            
            # 주식 리스트에서 추가 정보 가져오기
            stock_list_info = STOCK_LIST_MANAGER.find_stock_info(symbol)
            
            # 기본 정보 추출
            stock_info = {
                'symbol': symbol,
                'name': stock_list_info.get('name', info.get('shortName', 'N/A')),
                'market_cap': info.get('marketCap', 0),
                'volume': info.get('volume', 0),
                'avg_volume': info.get('averageVolume', 0),
                'price': info.get('currentPrice', 0),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'float_shares': info.get('floatShares', 0),
                'shares_outstanding': info.get('sharesOutstanding', 0),
                # 주식 리스트 정보 추가
                'market': stock_list_info.get('market', 'unknown'),
                'category': stock_list_info.get('category', 'unknown'),
                'subcategory': stock_list_info.get('subcategory', 'unknown')
            }
            
            # 캐시에 저장
            STOCK_CACHE.save_stock_info(symbol, stock_info)
            
            return stock_info
            
        except Exception as e:
            print(f"주식 정보 수집 오류 ({symbol}): {e}")
            return {}
            
    def detect_small_cap_stocks(self, symbols: List[str], 
                              max_market_cap: float = 1e12,  # 1조원
                              min_volatility: float = 20.0) -> List[Dict]:
        """소형주/잡주 탐지 (개선된 정보 제공)"""
        small_caps = []
        total_symbols = len(symbols)
        processed = 0
        
        print(f"🔍 {total_symbols}개 종목 분석 시작...")
        
        for symbol in symbols:
            try:
                processed += 1
                print(f"📊 분석 진행: {processed}/{total_symbols} - {symbol}")
                
                # 주식 정보 수집
                stock_info = self.get_stock_info(symbol)
                if not stock_info:
                    print(f"⚠️ {symbol}: 정보 수집 실패")
                    continue
                    
                # 소형주 기준 검사
                market_cap = stock_info.get('market_cap', 0)
                
                if market_cap > 0 and market_cap <= max_market_cap:
                    # 캐시에서 가격 데이터 확인
                    if len(symbol) == 6 and symbol.isdigit():
                        ticker_symbol = f"{symbol}.KS"
                    else:
                        ticker_symbol = symbol
                    price_data = STOCK_CACHE.get_price_data(symbol, "3mo", max_age_hours=6)
                    
                    if price_data is None:
                        # 새로 다운로드
                        price_data = yf.download(ticker_symbol, period="3mo", progress=False)
                        if not price_data.empty:
                            STOCK_CACHE.save_price_data(symbol, "3mo", price_data)
                    
                    if not price_data.empty:
                        volatility_data = self.calculate_volatility(price_data, window=20)
                        if not volatility_data.empty and 'Close' in volatility_data.columns:
                            try:
                                current_volatility = float(volatility_data['Close'].iloc[-1])
                                
                                if not pd.isna(current_volatility) and current_volatility >= min_volatility:
                                    # 추가 정보 계산
                                    technical_indicators = self.get_technical_indicators(symbol)
                                    
                                    # 종합 정보
                                    enhanced_info = stock_info.copy()
                                    enhanced_info.update({
                                        'current_volatility': current_volatility,
                                        'volatility_rank': self.get_volatility_rank(current_volatility),
                                        'market_cap_tier': self.get_market_cap_tier(market_cap),
                                        'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                                    })
                                    enhanced_info.update(technical_indicators)
                                    
                                    small_caps.append(enhanced_info)
                                    print(f"✅ {symbol} ({stock_info.get('name', 'N/A')}): 변동성 {current_volatility:.1f}% - 조건 충족")
                                else:
                                    print(f"❌ {symbol}: 변동성 {current_volatility:.1f}% - 기준 미달")
                            except Exception as vol_error:
                                print(f"⚠️ {symbol}: 변동성 계산 오류 - {vol_error}")
                        else:
                            print(f"⚠️ {symbol}: 변동성 계산 실패")
                    else:
                        print(f"⚠️ {symbol}: 가격 데이터 없음")
                else:
                    market_cap_billion = market_cap / 1e8 if market_cap > 0 else 0
                    print(f"❌ {symbol}: 시가총액 {market_cap_billion:.0f}억원 - 대형주")
                            
                time.sleep(0.1)  # API 제한 방지
                
            except Exception as e:
                print(f"❌ 소형주 분석 오류 ({symbol}): {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # 변동성 기준으로 정렬
        small_caps.sort(key=lambda x: x.get('current_volatility', 0), reverse=True)
        
        print(f"🎯 분석 완료: {len(small_caps)}개 소형주 발견")
        return small_caps
    
    def get_market_cap_tier(self, market_cap: float) -> str:
        """시가총액 등급 분류"""
        if market_cap >= 1e12:  # 1조원 이상
            return "대형주"
        elif market_cap >= 5e11:  # 5000억원 이상
            return "중형주"
        elif market_cap >= 1e11:  # 1000억원 이상
            return "소형주"
        elif market_cap >= 5e10:  # 500억원 이상
            return "소소형주"
        else:
            return "극소형주"
        
    def get_volatility_rank(self, volatility: float) -> str:
        """변동성 등급 분류"""
        if volatility >= 50:
            return "극고변동성"
        elif volatility >= 35:
            return "고변동성"
        elif volatility >= 25:
            return "중변동성"
        elif volatility >= 15:
            return "저변동성"
        else:
            return "안정"
            
    def analyze_market_sentiment(self, volatility_indices: Dict[str, pd.DataFrame]) -> Dict[str, str]:
        """시장 심리 분석"""
        sentiment = {}
        
        try:
            # VIX 분석
            if 'VIX' in volatility_indices and not volatility_indices['VIX'].empty:
                vix_data = volatility_indices['VIX']
                if 'Close' in vix_data.columns and len(vix_data) > 0:
                    current_vix = float(vix_data['Close'].iloc[-1])
                    
                    if current_vix >= 30:
                        sentiment['VIX'] = "극도공포 (변동성 폭발 위험)"
                    elif current_vix >= 20:
                        sentiment['VIX'] = "공포 (높은 변동성)"
                    elif current_vix >= 15:
                        sentiment['VIX'] = "불안 (중간 변동성)"
                    else:
                        sentiment['VIX'] = "안정 (낮은 변동성)"
                    
            # KOSPI 변동성 분석
            if 'KOSPI_Volatility' in volatility_indices and not volatility_indices['KOSPI_Volatility'].empty:
                kospi_data = volatility_indices['KOSPI_Volatility']
                if 'Close' in kospi_data.columns and len(kospi_data) > 0:
                    current_kospi_vol = float(kospi_data['Close'].iloc[-1])
                    
                    if not np.isnan(current_kospi_vol):
                        if current_kospi_vol >= 25:
                            sentiment['KOSPI'] = "고변동성 (잡주 급등락 위험)"
                        elif current_kospi_vol >= 15:
                            sentiment['KOSPI'] = "중변동성 (주의 필요)"
                        else:
                            sentiment['KOSPI'] = "안정적"
                    
            # KOSDAQ 변동성 분석
            if 'KOSDAQ_Volatility' in volatility_indices and not volatility_indices['KOSDAQ_Volatility'].empty:
                kosdaq_data = volatility_indices['KOSDAQ_Volatility']
                if 'Close' in kosdaq_data.columns and len(kosdaq_data) > 0:
                    current_kosdaq_vol = float(kosdaq_data['Close'].iloc[-1])
                    
                    if not np.isnan(current_kosdaq_vol):
                        if current_kosdaq_vol >= 30:
                            sentiment['KOSDAQ'] = "극고변동성 (소형주 폭등락)"
                        elif current_kosdaq_vol >= 20:
                            sentiment['KOSDAQ'] = "고변동성 (테마주 활성)"
                        else:
                            sentiment['KOSDAQ'] = "안정적"
                            
            # 기본 메시지가 없으면 추가
            if not sentiment:
                sentiment['상태'] = "데이터 수집 중..."
                    
        except Exception as e:
            sentiment['오류'] = f"분석 실패: {str(e)}"
            print(f"시장 심리 분석 오류: {e}")
            import traceback
            traceback.print_exc()
            
        return sentiment
        
    def get_technical_indicators(self, symbol: str, period: str = "6mo") -> Dict:
        """기술적 지표 계산"""
        try:
            if len(symbol) == 6 and symbol.isdigit():
                ticker_symbol = f"{symbol}.KS"
            else:
                ticker_symbol = symbol
            data = yf.download(ticker_symbol, period=period, progress=False)
            
            if data.empty:
                return {}
                
            # 기술적 지표 계산
            indicators = {}
            
            # ATR (Average True Range) - 변동성
            high_low = data['High'] - data['Low']
            high_close = np.abs(data['High'] - data['Close'].shift())
            low_close = np.abs(data['Low'] - data['Close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = ranges.max(axis=1)
            atr = true_range.rolling(window=14).mean()
            
            # 볼린저 밴드
            sma_20 = data['Close'].rolling(window=20).mean()
            std_20 = data['Close'].rolling(window=20).std()
            bb_upper = sma_20 + (std_20 * 2)
            bb_lower = sma_20 - (std_20 * 2)
            
            # 0으로 나누기 방지
            bb_width = bb_upper - bb_lower
            bb_position = np.where(bb_width != 0, (data['Close'] - bb_lower) / bb_width, 0.5)
            
            # RSI
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            
            # 0으로 나누기 방지
            rs = np.where(loss != 0, gain / loss, 0)
            rsi = 100 - (100 / (1 + rs))
            
            # 최신 값들 (안전한 추출)
            def safe_get_last_value(series, default=0):
                try:
                    if isinstance(series, pd.Series) and len(series) > 0:
                        val = series.iloc[-1]
                        return float(val) if not np.isnan(val) else default
                    elif isinstance(series, np.ndarray) and len(series) > 0:
                        val = series[-1]
                        return float(val) if not np.isnan(val) else default
                    else:
                        return default
                except:
                    return default
            
            # 가격 변화율 계산 (안전)
            price_change_5d = 0
            if len(data) >= 6:
                try:
                    current_price = float(data['Close'].iloc[-1])
                    past_price = float(data['Close'].iloc[-6])
                    if past_price > 0:
                        price_change_5d = ((current_price / past_price) - 1) * 100
                except:
                    price_change_5d = 0
            
            # 거래량 비율 계산 (안전)
            volume_ratio = 1
            if len(data) >= 20:
                try:
                    recent_vol = data['Volume'].iloc[-5:].mean()
                    past_vol = data['Volume'].iloc[-20:].mean()
                    if past_vol > 0:
                        volume_ratio = recent_vol / past_vol
                except:
                    volume_ratio = 1
            
            indicators = {
                'ATR': safe_get_last_value(atr, 0),
                'ATR_percentage': (safe_get_last_value(atr, 0) / safe_get_last_value(data['Close'], 1) * 100) if safe_get_last_value(data['Close'], 0) > 0 else 0,
                'BB_position': safe_get_last_value(bb_position, 0.5),
                'RSI': safe_get_last_value(rsi, 50),
                'price_change_5d': price_change_5d,
                'volume_ratio': volume_ratio,
            }
            
            return indicators
            
        except Exception as e:
            print(f"기술적 지표 계산 오류 ({symbol}): {e}")
            return {}
            
    def comprehensive_volatility_analysis(self, symbols: List[str]) -> Dict:
        """종합 변동성 분석"""
        
        # 1. 변동성 지수 수집
        volatility_indices = self.get_volatility_indices(period="3mo")
        
        # 2. 시장 심리 분석
        market_sentiment = self.analyze_market_sentiment(volatility_indices)
        
        # 3. 소형주 탐지
        small_caps = self.detect_small_cap_stocks(symbols, max_market_cap=5e11, min_volatility=20.0)
        
        # 4. 상위 변동성 종목들의 기술적 지표 분석
        top_volatile_stocks = small_caps[:10]  # 상위 10개
        for stock in top_volatile_stocks:
            technical = self.get_technical_indicators(stock['symbol'])
            stock.update(technical)
            
        # 5. 종합 분석 결과
        analysis_result = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'volatility_indices': volatility_indices,
            'market_sentiment': market_sentiment,
            'small_cap_count': len(small_caps),
            'top_volatile_stocks': top_volatile_stocks,
            'analysis_summary': self.generate_analysis_summary(market_sentiment, small_caps)
        }
        
        return analysis_result
        
    def generate_analysis_summary(self, market_sentiment: Dict, small_caps: List[Dict]) -> str:
        """분석 요약 생성"""
        summary_parts = []
        
        # 시장 상황 요약
        if 'VIX' in market_sentiment:
            summary_parts.append(f"• 글로벌 변동성(VIX): {market_sentiment['VIX']}")
            
        if 'KOSPI' in market_sentiment:
            summary_parts.append(f"• KOSPI 변동성: {market_sentiment['KOSPI']}")
            
        if 'KOSDAQ' in market_sentiment:
            summary_parts.append(f"• KOSDAQ 변동성: {market_sentiment['KOSDAQ']}")
            
        # 잡주 현황
        if small_caps:
            high_vol_count = len([s for s in small_caps if isinstance(s.get('current_volatility', 0), (int, float)) and s.get('current_volatility', 0) >= 35])
            summary_parts.append(f"• 고변동성 소형주: {high_vol_count}개 발견")
            
            if high_vol_count > 5:
                summary_parts.append("• ⚠️ 잡주 급등락 위험 구간")
            elif high_vol_count > 2:
                summary_parts.append("• 📈 테마주 활성화 구간")
            else:
                summary_parts.append("• 📊 정상 변동성 구간")
        else:
            summary_parts.append("• 소형주 데이터 부족")
            
        return "\n".join(summary_parts)


# 전역 인스턴스
VOLATILITY_ANALYZER = VolatilityAnalyzer()

# 한국 주요 소형주/테마주 심볼 목록 (예시)
KOREAN_SMALL_CAP_SYMBOLS = [
    # IT/테크 소형주
    "060310", "095570", "078340", "052690", "036810",  # 3S, AJ네트웍스, 컴투스, 한전기술, 에프텍
    "207940", "068270", "196170", "214450", "145020",  # 삼성바이오로직스, 셀트리온, 알테오젠, 파마리서치, 휴젤
    "259960", "194480", "112040", "078340", "053800",  # 크래프톤, 데브시스터즈, 위메이드, 컴투스, 마니커
    "009540", "267250", "010620", "079550", "051600",  # HD한국조선해양, HD현대중공업, 현대미포조선, LIG넥스원, 한국선재
    "336260", "052690", "095910", "033240", "018470",  # 두산에너빌리티, 한전기술, JW신약, 자화전자, 삼화페인트
]
