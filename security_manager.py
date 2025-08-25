"""
보안 관리자
- 대량 입력 방지
- 스팸 방지
- 데이터 검증
- 백업 및 복구
"""

import time
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import streamlit as st
import hashlib

class SecurityManager:
    def __init__(self):
        self.rate_limit_file = "rate_limits.json"
        self.backup_dir = "backups"
        self.max_tickers_per_user = 50  # 사용자당 최대 티커 수
        self.max_tickers_total = 500    # 전체 최대 티커 수
        self.rate_limit_window = 300    # 5분 (초)
        self.max_requests_per_window = 20  # 5분당 최대 요청 수
        self.ensure_backup_dir()
    
    def ensure_backup_dir(self):
        """백업 디렉토리 생성"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def get_client_id(self) -> str:
        """클라이언트 식별자 생성 (IP 기반)"""
        # Streamlit에서 실제 IP를 가져오기 어려우므로 세션 ID 사용
        if 'client_id' not in st.session_state:
            # 세션 시작 시간과 랜덤 값으로 고유 ID 생성
            session_data = f"{time.time()}_{hash(str(st.session_state))}"
            st.session_state.client_id = hashlib.md5(session_data.encode()).hexdigest()[:12]
        return st.session_state.client_id
    
    def load_rate_limits(self) -> Dict:
        """레이트 리미트 데이터 로드"""
        try:
            if os.path.exists(self.rate_limit_file):
                with open(self.rate_limit_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {}
    
    def save_rate_limits(self, data: Dict):
        """레이트 리미트 데이터 저장"""
        try:
            with open(self.rate_limit_file, 'w') as f:
                json.dump(data, f)
        except:
            pass
    
    def cleanup_old_records(self, data: Dict) -> Dict:
        """오래된 레이트 리미트 기록 정리"""
        current_time = time.time()
        cutoff_time = current_time - self.rate_limit_window
        
        cleaned_data = {}
        for client_id, records in data.items():
            # 최근 기록만 유지
            recent_records = [r for r in records if r > cutoff_time]
            if recent_records:
                cleaned_data[client_id] = recent_records
        
        return cleaned_data
    
    def check_rate_limit(self, client_id: str) -> Tuple[bool, str]:
        """레이트 리미트 검사"""
        current_time = time.time()
        data = self.load_rate_limits()
        data = self.cleanup_old_records(data)
        
        if client_id not in data:
            data[client_id] = []
        
        # 현재 윈도우 내의 요청 수 확인
        window_start = current_time - self.rate_limit_window
        recent_requests = [r for r in data[client_id] if r > window_start]
        
        if len(recent_requests) >= self.max_requests_per_window:
            remaining_time = int(self.rate_limit_window - (current_time - min(recent_requests)))
            return False, f"⚠️ 요청 한도 초과. {remaining_time}초 후 다시 시도하세요."
        
        # 새 요청 기록
        data[client_id].append(current_time)
        self.save_rate_limits(data)
        
        return True, ""
    
    def check_ticker_limits(self, current_tickers: Dict, new_ticker_count: int = 1) -> Tuple[bool, str]:
        """티커 개수 제한 검사"""
        client_id = self.get_client_id()
        
        # 전체 티커 수 제한
        total_count = len(current_tickers)
        if total_count + new_ticker_count > self.max_tickers_total:
            return False, f"⚠️ 전체 티커 한도 초과 ({self.max_tickers_total}개 제한)"
        
        # 사용자별 티커 수 제한 (세션 기반)
        user_tickers = 0
        if 'custom_tickers' in st.session_state:
            user_tickers = len(st.session_state.custom_tickers)
        
        if user_tickers + new_ticker_count > self.max_tickers_per_user:
            return False, f"⚠️ 개인 티커 한도 초과 ({self.max_tickers_per_user}개 제한)"
        
        return True, ""
    
    def validate_input_safety(self, ticker: str, sector: str = None) -> Tuple[bool, str]:
        """입력 데이터 안전성 검증"""
        # 티커 길이 제한
        if len(ticker) > 10:
            return False, "⚠️ 티커는 10자를 초과할 수 없습니다"
        
        # 특수문자 제한
        if not ticker.replace('-', '').replace('.', '').isalnum():
            return False, "⚠️ 티커에 허용되지 않는 문자가 포함되어 있습니다"
        
        # 섹터 검증
        if sector:
            valid_sectors = [
                "🌾 농업/식품", "🏭 산업/제조", "🛒 소비재", "🏥 헬스케어",
                "💻 기술", "🏦 금융", "⚡ 에너지", "🏠 부동산/REIT",
                "🔌 유틸리티", "📱 통신/미디어"
            ]
            if sector not in valid_sectors:
                return False, "⚠️ 유효하지 않은 섹터입니다"
        
        return True, ""
    
    def create_backup(self, data: Dict, backup_type: str = "manual") -> str:
        """데이터 백업 생성"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backup_{backup_type}_{timestamp}.json"
            filepath = os.path.join(self.backup_dir, filename)
            
            backup_data = {
                'timestamp': timestamp,
                'type': backup_type,
                'data': data,
                'metadata': {
                    'ticker_count': len(data.get('custom_tickers', {})),
                    'client_id': self.get_client_id()
                }
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            return filepath
        except Exception as e:
            return f"백업 생성 오류: {str(e)}"
    
    def list_backups(self) -> List[Dict]:
        """백업 목록 조회"""
        backups = []
        try:
            if not os.path.exists(self.backup_dir):
                return backups
            
            for filename in os.listdir(self.backup_dir):
                if filename.endswith('.json') and filename.startswith('backup_'):
                    filepath = os.path.join(self.backup_dir, filename)
                    stat = os.stat(filepath)
                    
                    # 파일에서 메타데이터 읽기
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            backup_data = json.load(f)
                        
                        backups.append({
                            'filename': filename,
                            'filepath': filepath,
                            'size': stat.st_size,
                            'created': datetime.fromtimestamp(stat.st_mtime),
                            'type': backup_data.get('type', 'unknown'),
                            'ticker_count': backup_data.get('metadata', {}).get('ticker_count', 0)
                        })
                    except:
                        # 메타데이터를 읽을 수 없는 경우 기본 정보만
                        backups.append({
                            'filename': filename,
                            'filepath': filepath,
                            'size': stat.st_size,
                            'created': datetime.fromtimestamp(stat.st_mtime),
                            'type': 'unknown',
                            'ticker_count': 0
                        })
            
            # 최신순 정렬
            backups.sort(key=lambda x: x['created'], reverse=True)
            
        except Exception as e:
            st.error(f"백업 목록 조회 오류: {str(e)}")
        
        return backups
    
    def restore_from_backup(self, backup_filepath: str) -> Tuple[bool, str, Dict]:
        """백업에서 복원"""
        try:
            with open(backup_filepath, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            restored_data = backup_data.get('data', {})
            ticker_count = len(restored_data.get('custom_tickers', {}))
            
            return True, f"✅ 백업 복원 성공 ({ticker_count}개 티커)", restored_data
            
        except Exception as e:
            return False, f"❌ 백업 복원 오류: {str(e)}", {}
    
    def auto_backup_if_needed(self, current_data: Dict):
        """필요시 자동 백업"""
        try:
            # 마지막 자동 백업 시간 확인
            last_backup_file = os.path.join(self.backup_dir, "last_auto_backup.txt")
            
            should_backup = False
            if os.path.exists(last_backup_file):
                with open(last_backup_file, 'r') as f:
                    last_backup_time = float(f.read().strip())
                
                # 24시간마다 자동 백업
                if time.time() - last_backup_time > 86400:  # 24시간
                    should_backup = True
            else:
                should_backup = True
            
            if should_backup:
                backup_path = self.create_backup(current_data, "auto")
                
                # 마지막 백업 시간 기록
                with open(last_backup_file, 'w') as f:
                    f.write(str(time.time()))
                
                # 오래된 자동 백업 정리 (최근 7개만 유지)
                self.cleanup_old_backups("auto", keep_count=7)
                
        except Exception as e:
            pass  # 자동 백업 실패는 조용히 처리
    
    def cleanup_old_backups(self, backup_type: str, keep_count: int = 7):
        """오래된 백업 정리"""
        try:
            backups = [b for b in self.list_backups() if b['type'] == backup_type]
            
            if len(backups) > keep_count:
                # 오래된 백업 삭제
                for backup in backups[keep_count:]:
                    os.remove(backup['filepath'])
                    
        except Exception as e:
            pass  # 정리 실패는 조용히 처리
    
    def get_security_status(self) -> Dict:
        """보안 상태 정보 반환"""
        client_id = self.get_client_id()
        rate_data = self.load_rate_limits()
        rate_data = self.cleanup_old_records(rate_data)
        
        current_requests = len(rate_data.get(client_id, []))
        remaining_requests = max(0, self.max_requests_per_window - current_requests)
        
        backups = self.list_backups()
        
        return {
            'client_id': client_id,
            'current_requests': current_requests,
            'remaining_requests': remaining_requests,
            'max_requests': self.max_requests_per_window,
            'window_minutes': self.rate_limit_window // 60,
            'backup_count': len(backups),
            'last_backup': backups[0]['created'] if backups else None,
            'max_tickers_total': self.max_tickers_total,
            'max_tickers_per_user': self.max_tickers_per_user
        }

# 전역 보안 관리자 인스턴스
SECURITY = SecurityManager()

def check_security_before_action(action_type: str = "add_ticker") -> Tuple[bool, str]:
    """액션 실행 전 보안 검사"""
    client_id = SECURITY.get_client_id()
    
    # 레이트 리미트 검사
    rate_ok, rate_msg = SECURITY.check_rate_limit(client_id)
    if not rate_ok:
        return False, rate_msg
    
    return True, ""

def display_security_status():
    """보안 상태 표시"""
    status = SECURITY.get_security_status()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "요청 잔여", 
            f"{status['remaining_requests']}/{status['max_requests']}",
            help=f"{status['window_minutes']}분당 제한"
        )
    
    with col2:
        st.metric(
            "최대 티커", 
            f"{status['max_tickers_total']}개",
            help="전체 시스템 제한"
        )
    
    with col3:
        st.metric(
            "개인 한도", 
            f"{status['max_tickers_per_user']}개",
            help="사용자별 제한"
        )
    
    with col4:
        st.metric(
            "백업 개수", 
            f"{status['backup_count']}개",
            help="생성된 백업 파일 수"
        )
    
    # 세션 정보를 간단하게 표시 (화살표 문제 해결)
    st.markdown("**🔍 세션 정보**")
    info_text = f"세션 ID: `{status['client_id']}`"
    if status['last_backup']:
        info_text += f" | 마지막 백업: {status['last_backup']}"
    st.markdown(info_text)
