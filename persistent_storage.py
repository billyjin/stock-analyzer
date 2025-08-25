"""
영구 저장소 관리
- JSON 파일 기반 로컬 저장
- SQLite 데이터베이스 저장 (향후 확장)
- 클라우드 저장소 연동 (향후 확장)
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
import streamlit as st

class PersistentStorage:
    def __init__(self, storage_file: str = "custom_tickers.json"):
        self.storage_file = storage_file
        self.ensure_storage_exists()
    
    def ensure_storage_exists(self):
        """저장소 파일이 없으면 생성"""
        if not os.path.exists(self.storage_file):
            self.save_data({})
    
    def load_data(self) -> Dict[str, Any]:
        """저장된 데이터 로드"""
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def save_data(self, data: Dict[str, Any]) -> bool:
        """데이터 저장"""
        try:
            # 백업 생성
            if os.path.exists(self.storage_file):
                backup_file = f"{self.storage_file}.backup"
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    backup_data = f.read()
                with open(backup_file, 'w', encoding='utf-8') as f:
                    f.write(backup_data)
            
            # 새 데이터 저장
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            st.error(f"데이터 저장 오류: {str(e)}")
            return False
    
    def load_custom_tickers(self) -> Dict[str, Dict]:
        """커스텀 티커 목록 로드"""
        data = self.load_data()
        return data.get('custom_tickers', {})
    
    def save_custom_tickers(self, tickers: Dict[str, Dict]) -> bool:
        """커스텀 티커 목록 저장"""
        data = self.load_data()
        data['custom_tickers'] = tickers
        data['last_updated'] = datetime.now().isoformat()
        return self.save_data(data)
    
    def add_ticker(self, ticker: str, info: Dict) -> bool:
        """단일 티커 추가"""
        tickers = self.load_custom_tickers()
        tickers[ticker] = info
        return self.save_custom_tickers(tickers)
    
    def remove_ticker(self, ticker: str) -> bool:
        """단일 티커 제거"""
        tickers = self.load_custom_tickers()
        if ticker in tickers:
            del tickers[ticker]
            return self.save_custom_tickers(tickers)
        return False
    
    def update_ticker(self, ticker: str, info: Dict) -> bool:
        """단일 티커 정보 업데이트"""
        tickers = self.load_custom_tickers()
        if ticker in tickers:
            tickers[ticker].update(info)
            return self.save_custom_tickers(tickers)
        return False
    
    def sync_with_session_state(self):
        """세션 상태와 영구 저장소 동기화"""
        # 영구 저장소에서 로드
        persistent_tickers = self.load_custom_tickers()
        
        # 세션 상태 초기화 또는 병합
        if 'custom_tickers' not in st.session_state:
            st.session_state.custom_tickers = {}
        
        # 영구 저장소의 데이터를 세션 상태에 병합
        st.session_state.custom_tickers.update(persistent_tickers)
        
        # 세션 상태의 변경사항을 영구 저장소에 저장
        if st.session_state.custom_tickers != persistent_tickers:
            self.save_custom_tickers(st.session_state.custom_tickers)
    
    def clear_all_data(self) -> bool:
        """모든 데이터 삭제"""
        try:
            if os.path.exists(self.storage_file):
                os.remove(self.storage_file)
            self.ensure_storage_exists()
            if 'custom_tickers' in st.session_state:
                st.session_state.custom_tickers = {}
            return True
        except Exception as e:
            st.error(f"데이터 삭제 오류: {str(e)}")
            return False
    
    def get_storage_info(self) -> Dict[str, Any]:
        """저장소 정보 반환"""
        data = self.load_data()
        tickers = data.get('custom_tickers', {})
        
        return {
            'file_path': os.path.abspath(self.storage_file),
            'file_exists': os.path.exists(self.storage_file),
            'file_size': os.path.getsize(self.storage_file) if os.path.exists(self.storage_file) else 0,
            'ticker_count': len(tickers),
            'last_updated': data.get('last_updated', 'N/A'),
            'tickers': list(tickers.keys())
        }

# 전역 저장소 인스턴스
STORAGE = PersistentStorage()

def initialize_persistent_storage():
    """앱 시작 시 영구 저장소 초기화"""
    STORAGE.sync_with_session_state()

def save_session_to_persistent():
    """세션 상태를 영구 저장소에 저장"""
    if 'custom_tickers' in st.session_state:
        STORAGE.save_custom_tickers(st.session_state.custom_tickers)

def display_storage_info():
    """저장소 정보 표시"""
    info = STORAGE.get_storage_info()
    
    st.info(f"""
    📁 **저장소 정보**
    - 파일 경로: `{info['file_path']}`
    - 파일 크기: {info['file_size']} bytes
    - 커스텀 티커 수: {info['ticker_count']}개
    - 마지막 업데이트: {info['last_updated']}
    """)
    
    if info['tickers']:
        with st.expander("📋 저장된 티커 목록"):
            st.write(", ".join(info['tickers']))
