"""
Ticker 관리 시스템
- Ticker 유효성 검증
- 섹터 자동 분류
- 엑셀 파일 관리
- Google Sheets 연동
"""

import yfinance as yf
import pandas as pd
import streamlit as st
import re
from typing import Dict, List, Tuple, Optional
import io
import json
from datetime import datetime
from persistent_storage import STORAGE, initialize_persistent_storage, save_session_to_persistent, display_storage_info
from security_manager import SECURITY, check_security_before_action, display_security_status

# Google Sheets 연동을 위한 선택적 import
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False

class TickerManager:
    def __init__(self):
        # 기본 섹터 분류 규칙
        self.sector_keywords = {
            "🌾 농업/식품": [
                'food', 'agriculture', 'grain', 'meat', 'dairy', 'beverage', 'restaurant',
                'grocery', 'farming', 'crop', 'livestock', 'fertilizer', 'seed'
            ],
            "🏭 산업/제조": [
                'industrial', 'manufacturing', 'machinery', 'aerospace', 'defense',
                'transportation', 'logistics', 'shipping', 'construction', 'materials'
            ],
            "🛒 소비재": [
                'consumer', 'retail', 'apparel', 'household', 'personal care',
                'cosmetics', 'entertainment', 'media', 'gaming'
            ],
            "🏥 헬스케어": [
                'healthcare', 'pharmaceutical', 'biotech', 'medical', 'hospital',
                'drug', 'therapy', 'diagnostic', 'device'
            ],
            "💻 기술": [
                'technology', 'software', 'hardware', 'semiconductor', 'internet',
                'cloud', 'ai', 'artificial intelligence', 'cybersecurity', 'data'
            ],
            "🏦 금융": [
                'financial', 'bank', 'insurance', 'investment', 'credit', 'payment',
                'fintech', 'asset management', 'real estate investment'
            ],
            "⚡ 에너지": [
                'energy', 'oil', 'gas', 'renewable', 'solar', 'wind', 'nuclear',
                'coal', 'utility', 'power', 'electric'
            ],
            "🏠 부동산/REIT": [
                'real estate', 'reit', 'property', 'residential', 'commercial',
                'land', 'construction', 'development'
            ],
            "🔌 유틸리티": [
                'utility', 'electric', 'water', 'gas', 'telecommunications',
                'infrastructure', 'pipeline'
            ],
            "📱 통신/미디어": [
                'telecommunications', 'wireless', 'broadband', 'cable', 'satellite',
                'media', 'broadcasting', 'streaming', 'social media'
            ]
        }
        
        # 알려진 티커별 섹터 매핑 (우선순위 높음)
        self.known_tickers = {
            # 농업/식품
            'DE': '🌾 농업/식품', 'ADM': '🌾 농업/식품', 'TSN': '🌾 농업/식품',
            'WMT': '🌾 농업/식품', 'COST': '🌾 농업/식품', 'KR': '🌾 농업/식품',
            'MCD': '🌾 농업/식품', 'SBUX': '🌾 농업/식품', 'KO': '🌾 농업/식품',
            'PEP': '🌾 농업/식품', 'GIS': '🌾 농업/식품', 'K': '🌾 농업/식품',
            
            # 기술
            'AAPL': '💻 기술', 'MSFT': '💻 기술', 'GOOGL': '💻 기술', 'GOOG': '💻 기술',
            'AMZN': '💻 기술', 'META': '💻 기술', 'TSLA': '💻 기술', 'NVDA': '💻 기술',
            'AMD': '💻 기술', 'INTC': '💻 기술', 'CRM': '💻 기술', 'ADBE': '💻 기술',
            
            # 헬스케어
            'JNJ': '🏥 헬스케어', 'PFE': '🏥 헬스케어', 'UNH': '🏥 헬스케어',
            'ABT': '🏥 헬스케어', 'MRK': '🏥 헬스케어', 'TMO': '🏥 헬스케어',
            
            # 금융
            'JPM': '🏦 금융', 'BAC': '🏦 금융', 'WFC': '🏦 금융', 'GS': '🏦 금융',
            'MS': '🏦 금융', 'V': '🏦 금융', 'MA': '🏦 금융', 'AXP': '🏦 금융',
            
            # 에너지
            'XOM': '⚡ 에너지', 'CVX': '⚡ 에너지', 'COP': '⚡ 에너지',
            'SLB': '⚡ 에너지', 'EOG': '⚡ 에너지',
            
            # 산업/제조
            'CAT': '🏭 산업/제조', 'BA': '🏭 산업/제조', 'HON': '🏭 산업/제조',
            'MMM': '🏭 산업/제조', 'GE': '🏭 산업/제조', 'LMT': '🏭 산업/제조',
        }

    def validate_ticker(self, ticker: str) -> Tuple[bool, str, Dict]:
        """
        Ticker 유효성 검증
        Returns: (is_valid, error_message, stock_info)
        """
        ticker = ticker.strip().upper()
        
        # 기본 형식 검증
        if not ticker:
            return False, "티커가 비어있습니다", {}
        
        if not re.match(r'^[A-Z]{1,5}$', ticker):
            return False, f"잘못된 티커 형식: {ticker} (영문 대문자 1-5자리만 허용)", {}
        
        try:
            # yfinance로 실제 데이터 확인
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # 기본 정보가 있는지 확인
            if not info or 'symbol' not in info:
                return False, f"존재하지 않는 티커: {ticker}", {}
            
            # 최근 가격 데이터 확인
            hist = stock.history(period="5d")
            if hist.empty:
                return False, f"가격 데이터가 없는 티커: {ticker}", {}
            
            return True, "", info
            
        except Exception as e:
            return False, f"티커 검증 오류 ({ticker}): {str(e)}", {}

    def classify_sector(self, ticker: str, stock_info: Dict) -> str:
        """
        주식 정보를 바탕으로 섹터 자동 분류
        """
        ticker = ticker.upper()
        
        # 1. 알려진 티커 우선 확인
        if ticker in self.known_tickers:
            return self.known_tickers[ticker]
        
        # 2. 주식 정보에서 섹터/산업 정보 추출
        sector_info = ""
        industry_info = ""
        business_summary = ""
        
        if stock_info:
            sector_info = stock_info.get('sector', '').lower()
            industry_info = stock_info.get('industry', '').lower()
            business_summary = stock_info.get('businessSummary', '').lower()
        
        search_text = f"{sector_info} {industry_info} {business_summary}"
        
        # 3. 키워드 매칭
        best_match = "🛒 소비재"  # 기본값
        max_matches = 0
        
        for sector, keywords in self.sector_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in search_text)
            if matches > max_matches:
                max_matches = matches
                best_match = sector
        
        return best_match

    def add_ticker(self, ticker: str, sector: str = None) -> Tuple[bool, str]:
        """
        새로운 티커 추가 (보안 검증 + 영구 저장 포함)
        """
        # 보안 검증
        security_ok, security_msg = check_security_before_action("add_ticker")
        if not security_ok:
            return False, security_msg
        
        # 입력 안전성 검증
        safe_ok, safe_msg = SECURITY.validate_input_safety(ticker, sector)
        if not safe_ok:
            return False, safe_msg
        
        # 티커 개수 제한 검증
        current_tickers = STORAGE.load_custom_tickers()
        limit_ok, limit_msg = SECURITY.check_ticker_limits(current_tickers, 1)
        if not limit_ok:
            return False, limit_msg
        
        # 기존 유효성 검증
        is_valid, error_msg, stock_info = self.validate_ticker(ticker)
        if not is_valid:
            return False, error_msg
        
        # 중복 확인
        if ticker.upper() in current_tickers:
            return False, f"⚠️ {ticker}는 이미 추가된 티커입니다"
        
        # 섹터 자동 분류 (섹터가 지정되지 않은 경우)
        if not sector:
            sector = self.classify_sector(ticker, stock_info)
        
        # 자동 백업 (필요시)
        all_data = {'custom_tickers': current_tickers}
        SECURITY.auto_backup_if_needed(all_data)
        
        # 세션 상태에 커스텀 티커 저장
        if 'custom_tickers' not in st.session_state:
            st.session_state.custom_tickers = {}
        
        ticker_info = {
            'sector': sector,
            'name': stock_info.get('longName', ticker),
            'added_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'added_by': SECURITY.get_client_id()  # 추가한 사용자 추적
        }
        
        st.session_state.custom_tickers[ticker] = ticker_info
        
        # 영구 저장소에도 저장
        STORAGE.add_ticker(ticker, ticker_info)
        
        return True, f"✅ {ticker} ({stock_info.get('longName', ticker)}) → {sector}"

    def remove_ticker(self, ticker: str) -> bool:
        """티커 제거 (영구 저장소에서도 제거)"""
        if 'custom_tickers' not in st.session_state:
            return False
        
        ticker = ticker.upper()
        if ticker in st.session_state.custom_tickers:
            del st.session_state.custom_tickers[ticker]
            # 영구 저장소에서도 제거
            STORAGE.remove_ticker(ticker)
            return True
        return False

    def get_all_tickers(self) -> Dict[str, Dict]:
        """모든 티커 목록 반환 (기본 + 커스텀)"""
        # 기본 티커들
        from stock_webapp import STOCK_SECTORS
        all_tickers = {}
        
        for sector, stocks in STOCK_SECTORS.items():
            for ticker, name in stocks.items():
                all_tickers[ticker] = {
                    'sector': sector,
                    'name': name,
                    'type': 'default'
                }
        
        # 커스텀 티커들 추가
        if 'custom_tickers' in st.session_state:
            for ticker, info in st.session_state.custom_tickers.items():
                all_tickers[ticker] = {
                    'sector': info['sector'],
                    'name': info['name'],
                    'type': 'custom',
                    'added_date': info['added_date']
                }
        
        return all_tickers

    def export_to_excel(self) -> bytes:
        """엑셀 파일로 내보내기"""
        all_tickers = self.get_all_tickers()
        
        data = []
        for ticker, info in all_tickers.items():
            data.append({
                '티커': ticker,
                '회사명': info['name'],
                '분석섹터': info['sector'],
                '타입': info['type'],
                '추가일시': info.get('added_date', '')
            })
        
        df = pd.DataFrame(data)
        
        # 엑셀 파일로 변환
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Ticker_List')
        
        return output.getvalue()

    def import_from_excel(self, uploaded_file) -> Tuple[bool, str, int]:
        """엑셀 파일에서 가져오기"""
        try:
            df = pd.read_excel(uploaded_file)
            
            required_columns = ['티커', '분석섹터']
            if not all(col in df.columns for col in required_columns):
                return False, f"필수 컬럼이 없습니다: {required_columns}", 0
            
            added_count = 0
            errors = []
            
            for _, row in df.iterrows():
                ticker = str(row['티커']).strip().upper()
                sector = str(row['분석섹터']).strip()
                
                if ticker == 'NAN' or not ticker:
                    continue
                
                # 티커 유효성 검증
                is_valid, error_msg, stock_info = self.validate_ticker(ticker)
                if is_valid:
                    # 세션 상태에 추가
                    if 'custom_tickers' not in st.session_state:
                        st.session_state.custom_tickers = {}
                    
                    st.session_state.custom_tickers[ticker] = {
                        'sector': sector,
                        'name': stock_info.get('longName', ticker),
                        'added_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    added_count += 1
                else:
                    errors.append(f"{ticker}: {error_msg}")
            
            error_msg = f"\n에러: {'; '.join(errors[:5])}" if errors else ""
            return True, f"✅ {added_count}개 티커 추가됨{error_msg}", added_count
            
        except Exception as e:
            return False, f"파일 처리 오류: {str(e)}", 0

    def connect_google_sheets(self, credentials_json: str, sheet_url: str) -> Tuple[bool, str, pd.DataFrame]:
        """Google Sheets 연동"""
        if not GSPREAD_AVAILABLE:
            return False, "Google Sheets 연동을 위해 gspread 패키지가 필요합니다. 'pip install gspread google-auth'로 설치하세요.", pd.DataFrame()
        
        try:
            # 서비스 계정 인증
            creds_dict = json.loads(credentials_json)
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            credentials = Credentials.from_service_account_info(creds_dict, scopes=scope)
            gc = gspread.authorize(credentials)
            
            # 스프레드시트 열기
            sheet = gc.open_by_url(sheet_url).sheet1
            data = sheet.get_all_records()
            
            df = pd.DataFrame(data)
            return True, "✅ Google Sheets 연결 성공", df
            
        except Exception as e:
            return False, f"Google Sheets 연결 오류: {str(e)}", pd.DataFrame()

# Streamlit UI 컴포넌트들
def ticker_management_ui():
    """티커 관리 UI"""
    # 간단하고 깔끔한 expander 스타일 (화살표 숨김)
    st.markdown("""
    <style>
    /* expander 깔끔한 스타일 */
    .streamlit-expanderHeader {
        background-color: #f8f9fa !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 6px !important;
        padding: 12px 16px !important;
        margin-bottom: 8px !important;
        font-weight: 500 !important;
    }
    
    .streamlit-expanderHeader:hover {
        background-color: #e9ecef !important;
    }
    
    .streamlit-expanderContent {
        padding: 16px !important;
        border: 1px solid #e0e0e0 !important;
        border-top: none !important;
        border-radius: 0 0 6px 6px !important;
        margin-bottom: 16px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.subheader("🔧 티커 관리")
    
    # 영구 저장소 초기화
    initialize_persistent_storage()
    
    ticker_mgr = TickerManager()
    
    # 보안 상태 표시
    st.markdown("#### 🛡️ 보안 상태")
    display_security_status()
    
    st.markdown("---")
    
    # 저장소 상태 표시
    col1, col2, col3 = st.columns(3)
    with col1:
        persistent_count = len(STORAGE.load_custom_tickers())
        st.metric("영구 저장된 티커", persistent_count)
    
    with col2:
        session_count = len(st.session_state.get('custom_tickers', {}))
        st.metric("세션 티커", session_count)
    
    with col3:
        if st.button("🔄 동기화"):
            initialize_persistent_storage()
            st.success("저장소와 세션 동기화 완료!")
            st.rerun()
    
    # 탭으로 기능 분리
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["➕ 티커 추가", "📊 현재 목록", "📁 파일 관리", "🔗 Google Sheets", "⚙️ 저장소 관리", "🔒 백업/복구"])
    
    with tab1:
        st.markdown("### 새 티커 추가")
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_ticker = st.text_input("티커 입력:", placeholder="예: AAPL, MSFT").upper()
        
        with col2:
            sector_options = list(ticker_mgr.sector_keywords.keys())
            manual_sector = st.selectbox("섹터 (자동분류 or 수동선택):", ["자동분류"] + sector_options)
        
        if st.button("✅ 티커 추가", type="primary"):
            if new_ticker:
                sector = None if manual_sector == "자동분류" else manual_sector
                success, message = ticker_mgr.add_ticker(new_ticker, sector)
                
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
        
        # 일괄 추가
        st.markdown("### 일괄 추가")
        bulk_tickers = st.text_area(
            "여러 티커 입력 (줄바꿈 또는 쉼표로 구분):",
            placeholder="AAPL\nMSFT,GOOGL\nTSLA"
        )
        
        if st.button("📝 일괄 추가"):
            if bulk_tickers:
                tickers = re.split(r'[,\n\r]+', bulk_tickers)
                tickers = [t.strip().upper() for t in tickers if t.strip()]
                
                results = []
                for ticker in tickers:
                    success, message = ticker_mgr.add_ticker(ticker)
                    results.append(message)
                
                for result in results:
                    if "✅" in result:
                        st.success(result)
                    else:
                        st.error(result)
                
                st.rerun()
    
    with tab2:
        st.markdown("### 현재 티커 목록")
        
        all_tickers = ticker_mgr.get_all_tickers()
        
        if all_tickers:
            # 필터링 옵션
            col1, col2, col3 = st.columns(3)
            
            with col1:
                filter_sector = st.selectbox("섹터 필터:", ["전체"] + list(ticker_mgr.sector_keywords.keys()))
            
            with col2:
                filter_type = st.selectbox("타입 필터:", ["전체", "기본", "커스텀"])
            
            with col3:
                search_ticker = st.text_input("티커 검색:", placeholder="AAPL")
            
            # 데이터 필터링
            filtered_data = []
            for ticker, info in all_tickers.items():
                # 섹터 필터
                if filter_sector != "전체" and info['sector'] != filter_sector:
                    continue
                
                # 타입 필터
                if filter_type == "기본" and info['type'] != 'default':
                    continue
                elif filter_type == "커스텀" and info['type'] != 'custom':
                    continue
                
                # 검색 필터
                if search_ticker and search_ticker.upper() not in ticker:
                    continue
                
                filtered_data.append({
                    '티커': ticker,
                    '회사명': info['name'],
                    '분석섹터': info['sector'],
                    '타입': info['type'],
                    '액션': '🗑️ 삭제' if info['type'] == 'custom' else '기본'
                })
            
            if filtered_data:
                df = pd.DataFrame(filtered_data)
                
                # 편집 가능한 데이터프레임 표시
                edited_df = st.data_editor(
                    df,
                    use_container_width=True,
                    disabled=["티커", "회사명", "타입"],
                    column_config={
                        "분석섹터": st.column_config.SelectboxColumn(
                            "분석섹터",
                            options=list(ticker_mgr.sector_keywords.keys())
                        ),
                        "액션": st.column_config.TextColumn("액션", disabled=True)
                    }
                )
                
                st.info(f"📊 총 {len(filtered_data)}개 티커 표시")
                
                # 변경사항 저장
                if st.button("💾 변경사항 저장"):
                    for idx, row in edited_df.iterrows():
                        ticker = row['티커']
                        new_sector = row['분석섹터']
                        
                        if ticker in st.session_state.get('custom_tickers', {}):
                            st.session_state.custom_tickers[ticker]['sector'] = new_sector
                    
                    st.success("✅ 변경사항이 저장되었습니다")
                    st.rerun()
                
                # 커스텀 티커 삭제
                custom_tickers = [row['티커'] for _, row in edited_df.iterrows() if row['타입'] == 'custom']
                if custom_tickers:
                    st.markdown("### 커스텀 티커 삭제")
                    ticker_to_delete = st.selectbox("삭제할 티커 선택:", custom_tickers)
                    
                    if st.button("🗑️ 삭제", type="secondary"):
                        if ticker_mgr.remove_ticker(ticker_to_delete):
                            st.success(f"✅ {ticker_to_delete} 삭제됨")
                            st.rerun()
            
            else:
                st.info("📭 필터 조건에 맞는 티커가 없습니다")
        
        else:
            st.info("📭 등록된 티커가 없습니다")
    
    with tab3:
        st.markdown("### 파일 관리")
        
        # 엑셀 파일 내보내기
        st.markdown("#### 📤 엑셀 파일 내보내기")
        
        if st.button("📊 현재 목록 엑셀로 내보내기"):
            excel_data = ticker_mgr.export_to_excel()
            
            st.download_button(
                label="💾 엑셀 파일 다운로드",
                data=excel_data,
                file_name=f"ticker_list_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        # 엑셀 파일 가져오기
        st.markdown("#### 📥 엑셀 파일 가져오기")
        st.info("필수 컬럼: 티커, 분석섹터 (선택: 회사명)")
        
        uploaded_file = st.file_uploader("엑셀 파일 선택:", type=['xlsx', 'xls'])
        
        if uploaded_file:
            if st.button("📋 파일에서 가져오기"):
                success, message, count = ticker_mgr.import_from_excel(uploaded_file)
                
                if success:
                    st.success(message)
                    if count > 0:
                        st.rerun()
                else:
                    st.error(message)
    
    with tab4:
        st.markdown("### Google Sheets 연동")
        
        if not GSPREAD_AVAILABLE:
            st.warning("⚠️ Google Sheets 연동을 위해 추가 패키지가 필요합니다.")
            st.code("pip install gspread google-auth")
            return
        
        # 도움말을 접기/펼치기 버튼으로 교체
        if st.button("❓ Google Sheets API 설정 도움말", key="google_help_toggle"):
            if 'show_google_help' not in st.session_state:
                st.session_state.show_google_help = True
            else:
                st.session_state.show_google_help = not st.session_state.show_google_help
        
        if st.session_state.get('show_google_help', False):
            st.markdown("""
            ## 🔑 Google Sheets API 서비스 계정 키 생성 방법

            ### 1️⃣ **Google Cloud Console 접속**
            1. [Google Cloud Console](https://console.cloud.google.com/)에 로그인
            2. 새 프로젝트 생성 또는 기존 프로젝트 선택

            ### 2️⃣ **Google Sheets API 활성화**
            1. **"API 및 서비스" → "라이브러리"** 클릭
            2. **"Google Sheets API"** 검색 → **"사용 설정"**
            3. **"Google Drive API"**도 같은 방법으로 활성화 (필수!)

            ### 3️⃣ **서비스 계정 생성**
            1. **"API 및 서비스" → "사용자 인증 정보"** 클릭
            2. **"+ 사용자 인증 정보 만들기" → "서비스 계정"** 선택
            3. 서비스 계정 정보 입력:
               - **서비스 계정 이름**: `ticker-manager`
               - **설명**: `Ticker 관리용 서비스 계정`
            4. **"만들기"** 클릭

            ### 4️⃣ **JSON 키 파일 다운로드**
            1. 생성된 서비스 계정 클릭
            2. **"키" 탭** → **"키 추가" → "새 키 만들기"**
            3. **"JSON"** 선택 → **"만들기"**
            4. JSON 파일이 자동으로 다운로드됩니다

            ### 5️⃣ **Google Sheets 공유 설정**
            1. 사용할 Google Sheets 파일 열기
            2. **"공유"** 버튼 클릭
            3. JSON 키의 **`client_email`** 주소를 **편집자** 권한으로 공유
               - 예: `ticker-manager@your-project.iam.gserviceaccount.com`

            ### 📋 **Google Sheets 형식**
            시트는 다음과 같은 컬럼으로 구성해주세요:

            | 티커 | 분석섹터 | 회사명 (선택) |
            |------|----------|---------------|
            | AAPL | 💻 기술 | Apple Inc. |
            | MSFT | 💻 기술 | Microsoft |
            | TSLA | 🛒 소비재 | Tesla |

            ### ⚠️ **보안 주의사항**
            - JSON 키는 **절대** 공개하지 마세요
            - 사용하지 않는 서비스 계정은 삭제하세요
            - 필요한 최소 권한만 부여하세요
            """)
        
        st.info("Google Sheets API 서비스 계정 키가 필요합니다")
        
        # 서비스 계정 키 입력
        creds_json = st.text_area(
            "서비스 계정 JSON 키:",
            placeholder='{"type": "service_account", ...}',
            height=150
        )
        
        # 시트 URL 입력
        sheet_url = st.text_input(
            "Google Sheets URL:",
            placeholder="https://docs.google.com/spreadsheets/d/..."
        )
        
        if st.button("🔗 Google Sheets에서 가져오기"):
            if creds_json and sheet_url:
                success, message, df = ticker_mgr.connect_google_sheets(creds_json, sheet_url)
                
                if success:
                    st.success(message)
                    st.dataframe(df.head())
                    
                    if st.button("📥 Google Sheets 데이터 가져오기"):
                        # Google Sheets 데이터를 커스텀 티커로 추가
                        # 구현 필요...
                        pass
                else:
                    st.error(message)
            else:
                st.warning("서비스 계정 키와 시트 URL을 모두 입력해주세요")
    
    with tab5:
        st.markdown("### 저장소 관리")
        
        # 저장소 정보 표시
        display_storage_info()
        
        st.markdown("---")
        
        # 저장소 동작 설명
        if st.button("ℹ️ 데이터 저장 방식 설명", key="storage_help_toggle"):
            if 'show_storage_help' not in st.session_state:
                st.session_state.show_storage_help = True
            else:
                st.session_state.show_storage_help = not st.session_state.show_storage_help
        
        if st.session_state.get('show_storage_help', False):
            st.markdown("""
            ## 🔄 **현재 데이터 저장 방식**
            
            ### ✅ **영구 저장** (모든 사용자 공유)
            - 추가된 티커는 **JSON 파일**에 영구 저장됩니다
            - **서버를 재시작해도 데이터 유지**
            - **모든 사용자가 동일한 티커 목록 공유**
            - 파일 위치: `custom_tickers.json`
            
            ### 🔄 **세션 동기화**
            - 페이지 로드 시 영구 저장소와 자동 동기화
            - 브라우저 새로고침해도 데이터 유지
            - 여러 탭에서 동시 사용 가능
            
            ### 📱 **다중 사용자 지원**
            - 한 사람이 추가한 티커는 **모든 사람에게 보임**
            - 실시간 동기화 (페이지 새로고침 필요)
            - 충돌 방지를 위한 안전한 저장
            
            ### 🚨 **주의사항**
            - 서버 파일 시스템에 저장되므로 **서버 백업 필수**
            - 대용량 데이터는 성능에 영향을 줄 수 있음
            - 동시 편집 시 마지막 저장이 우선됨
            """)
        
        st.markdown("---")
        
        # 수동 동기화
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 세션 → 영구저장소", help="현재 세션의 변경사항을 영구 저장소에 저장"):
                save_session_to_persistent()
                st.success("✅ 세션 데이터가 영구 저장소에 저장되었습니다")
        
        with col2:
            if st.button("📥 영구저장소 → 세션", help="영구 저장소의 데이터를 현재 세션에 로드"):
                initialize_persistent_storage()
                st.success("✅ 영구 저장소 데이터가 세션에 로드되었습니다")
                st.rerun()
        
        st.markdown("---")
        
        # 위험한 작업들
        st.markdown("### ⚠️ 위험한 작업")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ 모든 커스텀 티커 삭제", type="secondary"):
                if STORAGE.clear_all_data():
                    st.success("✅ 모든 커스텀 티커가 삭제되었습니다")
                    st.rerun()
                else:
                    st.error("❌ 삭제 중 오류가 발생했습니다")
        
        with col2:
            st.write("⚠️ 이 작업은 되돌릴 수 없습니다!")
    
    with tab6:
        st.markdown("### 백업 및 복구")
        
        # 수동 백업 생성
        st.markdown("#### 📦 수동 백업 생성")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 지금 백업 생성", type="primary"):
                current_data = {'custom_tickers': STORAGE.load_custom_tickers()}
                backup_path = SECURITY.create_backup(current_data, "manual")
                
                if backup_path.startswith("backup"):
                    st.success(f"✅ 백업 생성 완료: {backup_path}")
                else:
                    st.error(backup_path)
        
        with col2:
            st.info("💡 수동 백업은 중요한 변경 전에 생성하세요")
        
        st.markdown("---")
        
        # 백업 목록 및 복원
        st.markdown("#### 📋 백업 목록")
        backups = SECURITY.list_backups()
        
        if backups:
            # 백업 목록을 테이블로 표시
            backup_data = []
            for backup in backups:
                backup_data.append({
                    '파일명': backup['filename'],
                    '타입': backup['type'],
                    '생성일시': backup['created'].strftime('%Y-%m-%d %H:%M:%S'),
                    '티커 수': backup['ticker_count'],
                    '크기 (KB)': round(backup['size'] / 1024, 1)
                })
            
            backup_df = pd.DataFrame(backup_data)
            st.dataframe(backup_df, use_container_width=True)
            
            # 복원 기능
            st.markdown("#### 🔄 백업에서 복원")
            
            selected_backup = st.selectbox(
                "복원할 백업 선택:",
                options=range(len(backups)),
                format_func=lambda x: f"{backups[x]['filename']} ({backups[x]['created'].strftime('%Y-%m-%d %H:%M')})"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔄 선택한 백업으로 복원", type="secondary"):
                    # 복원 전 확인
                    if 'confirm_restore' not in st.session_state:
                        st.session_state.confirm_restore = False
                    
                    if not st.session_state.confirm_restore:
                        st.warning("⚠️ 복원하면 현재 데이터가 덮어씌워집니다!")
                        if st.button("⚠️ 확인 - 복원 실행"):
                            st.session_state.confirm_restore = True
                            st.rerun()
                    else:
                        backup_file = backups[selected_backup]['filepath']
                        success, message, restored_data = SECURITY.restore_from_backup(backup_file)
                        
                        if success:
                            # 복원된 데이터를 저장소에 적용
                            if 'custom_tickers' in restored_data:
                                STORAGE.save_custom_tickers(restored_data['custom_tickers'])
                                # 세션 상태도 업데이트
                                st.session_state.custom_tickers = restored_data['custom_tickers']
                            
                            st.success(message)
                            st.session_state.confirm_restore = False
                            st.rerun()
                        else:
                            st.error(message)
            
            with col2:
                st.info("💡 복원 전에 현재 데이터를 백업하는 것을 권장합니다")
        
        else:
            st.info("📭 생성된 백업이 없습니다")
        
        st.markdown("---")
        
        # 긴급 복구 기능
        st.markdown("#### 🚨 긴급 복구")
        
        if st.button("⚠️ 시스템 초기화 (위험)", key="emergency_help_toggle"):
            if 'show_emergency_help' not in st.session_state:
                st.session_state.show_emergency_help = True
            else:
                st.session_state.show_emergency_help = not st.session_state.show_emergency_help
        
        if st.session_state.get('show_emergency_help', False):
            st.markdown("""
            **이 기능은 다음과 같은 상황에서 사용하세요:**
            - 시스템이 해킹당했을 때
            - 대량의 스팸 데이터가 입력되었을 때
            - 데이터 손상으로 복구가 필요할 때
            
            **⚠️ 주의사항:**
            - 모든 커스텀 티커가 삭제됩니다
            - 백업도 모두 삭제됩니다
            - 되돌릴 수 없습니다
            """)
            
            emergency_code = st.text_input(
                "긴급 복구 코드 입력 (EMERGENCY_RESET):",
                type="password",
                placeholder="코드를 입력하세요"
            )
            
            if emergency_code == "EMERGENCY_RESET":
                if st.button("🚨 시스템 완전 초기화", type="secondary"):
                    # 모든 데이터 삭제
                    STORAGE.clear_all_data()
                    
                    # 백업 폴더 정리
                    import shutil
                    try:
                        if os.path.exists(SECURITY.backup_dir):
                            shutil.rmtree(SECURITY.backup_dir)
                        SECURITY.ensure_backup_dir()
                    except:
                        pass
                    
                    # 레이트 리미트 정리
                    try:
                        if os.path.exists(SECURITY.rate_limit_file):
                            os.remove(SECURITY.rate_limit_file)
                    except:
                        pass
                    
                    st.success("🚨 시스템이 완전히 초기화되었습니다")
                    st.info("페이지를 새로고침하세요")
            else:
                if emergency_code:
                    st.error("❌ 잘못된 긴급 복구 코드입니다")
        
        # 보안 설정
        st.markdown("---")
        st.markdown("#### 🛡️ 보안 설정")
        
        if st.button("🔧 보안 한도 조정 (관리자용)", key="security_settings_toggle"):
            if 'show_security_settings' not in st.session_state:
                st.session_state.show_security_settings = True
            else:
                st.session_state.show_security_settings = not st.session_state.show_security_settings
        
        if st.session_state.get('show_security_settings', False):
            st.markdown("현재 보안 설정:")
            st.write(f"- 전체 최대 티커: {SECURITY.max_tickers_total}개")
            st.write(f"- 사용자별 최대 티커: {SECURITY.max_tickers_per_user}개")
            st.write(f"- 레이트 리미트: {SECURITY.max_requests_per_window}회/{SECURITY.rate_limit_window//60}분")
            
            st.info("💡 보안 설정 변경은 코드 수정이 필요합니다")

if __name__ == "__main__":
    # 테스트용
    ticker_mgr = TickerManager()
    print(ticker_mgr.validate_ticker("AAPL"))
    print(ticker_mgr.classify_sector("AAPL", {"sector": "Technology", "industry": "Consumer Electronics"}))
