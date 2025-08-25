"""
주식 데이터 캐싱 시스템
중복 조회 방지 및 성능 향상을 위한 캐시 관리
"""

import json
import os
import pickle
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import pandas as pd

class StockDataCache:
    """주식 데이터 캐시 관리 클래스"""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, "stock_cache.json")
        self.data_dir = os.path.join(cache_dir, "data")
        
        # 캐시 디렉토리 생성
        os.makedirs(cache_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 캐시 메타데이터 로드
        self.cache_meta = self._load_cache_meta()
        
    def _load_cache_meta(self) -> Dict:
        """캐시 메타데이터 로드"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"캐시 메타데이터 로드 오류: {e}")
        
        return {}
    
    def _save_cache_meta(self):
        """캐시 메타데이터 저장"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_meta, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"캐시 메타데이터 저장 오류: {e}")
    
    def _get_cache_key(self, key_type: str, symbol: str, **kwargs) -> str:
        """캐시 키 생성"""
        params = "_".join([f"{k}_{v}" for k, v in sorted(kwargs.items())])
        return f"{key_type}_{symbol}_{params}" if params else f"{key_type}_{symbol}"
    
    def _is_cache_valid(self, cache_key: str, max_age_hours: int = 24) -> bool:
        """캐시 유효성 검사"""
        if cache_key not in self.cache_meta:
            return False
            
        cache_time = datetime.fromisoformat(self.cache_meta[cache_key]['timestamp'])
        expiry_time = cache_time + timedelta(hours=max_age_hours)
        
        return datetime.now() < expiry_time
    
    def get_stock_info(self, symbol: str, max_age_hours: int = 24) -> Optional[Dict]:
        """주식 정보 캐시에서 조회"""
        cache_key = self._get_cache_key("stock_info", symbol)
        
        if not self._is_cache_valid(cache_key, max_age_hours):
            return None
            
        try:
            data_file = os.path.join(self.data_dir, f"{cache_key}.json")
            if os.path.exists(data_file):
                with open(data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"캐시 데이터 로드 오류: {e}")
            
        return None
    
    def save_stock_info(self, symbol: str, data: Dict):
        """주식 정보 캐시에 저장"""
        cache_key = self._get_cache_key("stock_info", symbol)
        
        try:
            # 데이터 파일 저장
            data_file = os.path.join(self.data_dir, f"{cache_key}.json")
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 메타데이터 업데이트
            self.cache_meta[cache_key] = {
                'timestamp': datetime.now().isoformat(),
                'type': 'stock_info',
                'symbol': symbol,
                'file': f"{cache_key}.json"
            }
            
            self._save_cache_meta()
            
        except Exception as e:
            print(f"캐시 저장 오류: {e}")
    
    def get_price_data(self, symbol: str, period: str, max_age_hours: int = 6) -> Optional[pd.DataFrame]:
        """가격 데이터 캐시에서 조회"""
        cache_key = self._get_cache_key("price_data", symbol, period=period)
        
        if not self._is_cache_valid(cache_key, max_age_hours):
            return None
            
        try:
            data_file = os.path.join(self.data_dir, f"{cache_key}.pkl")
            if os.path.exists(data_file):
                return pd.read_pickle(data_file)
        except Exception as e:
            print(f"가격 데이터 캐시 로드 오류: {e}")
            
        return None
    
    def save_price_data(self, symbol: str, period: str, data: pd.DataFrame):
        """가격 데이터 캐시에 저장"""
        cache_key = self._get_cache_key("price_data", symbol, period=period)
        
        try:
            # 데이터 파일 저장 (pickle 사용)
            data_file = os.path.join(self.data_dir, f"{cache_key}.pkl")
            data.to_pickle(data_file)
            
            # 메타데이터 업데이트
            self.cache_meta[cache_key] = {
                'timestamp': datetime.now().isoformat(),
                'type': 'price_data',
                'symbol': symbol,
                'period': period,
                'file': f"{cache_key}.pkl"
            }
            
            self._save_cache_meta()
            
        except Exception as e:
            print(f"가격 데이터 캐시 저장 오류: {e}")
    
    def get_volatility_indices(self, period: str, max_age_hours: int = 1) -> Optional[Dict]:
        """변동성 지수 캐시에서 조회"""
        cache_key = self._get_cache_key("volatility_indices", "global", period=period)
        
        if not self._is_cache_valid(cache_key, max_age_hours):
            return None
            
        try:
            data_file = os.path.join(self.data_dir, f"{cache_key}.pkl")
            if os.path.exists(data_file):
                with open(data_file, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            print(f"변동성 지수 캐시 로드 오류: {e}")
            
        return None
    
    def save_volatility_indices(self, period: str, data: Dict):
        """변동성 지수 캐시에 저장"""
        cache_key = self._get_cache_key("volatility_indices", "global", period=period)
        
        try:
            # 데이터 파일 저장 (pickle 사용)
            data_file = os.path.join(self.data_dir, f"{cache_key}.pkl")
            with open(data_file, 'wb') as f:
                pickle.dump(data, f)
            
            # 메타데이터 업데이트
            self.cache_meta[cache_key] = {
                'timestamp': datetime.now().isoformat(),
                'type': 'volatility_indices',
                'period': period,
                'file': f"{cache_key}.pkl"
            }
            
            self._save_cache_meta()
            
        except Exception as e:
            print(f"변동성 지수 캐시 저장 오류: {e}")
    
    def clear_cache(self, older_than_hours: int = 168):  # 7일
        """오래된 캐시 정리"""
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        keys_to_remove = []
        
        for key, meta in self.cache_meta.items():
            cache_time = datetime.fromisoformat(meta['timestamp'])
            if cache_time < cutoff_time:
                keys_to_remove.append(key)
                
                # 파일 삭제
                try:
                    file_path = os.path.join(self.data_dir, meta['file'])
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as e:
                    print(f"캐시 파일 삭제 오류: {e}")
        
        # 메타데이터에서 제거
        for key in keys_to_remove:
            del self.cache_meta[key]
        
        self._save_cache_meta()
        
        return len(keys_to_remove)
    
    def get_cache_stats(self) -> Dict:
        """캐시 통계 정보"""
        stats = {
            'total_entries': len(self.cache_meta),
            'by_type': {},
            'cache_size_mb': 0
        }
        
        # 타입별 개수
        for meta in self.cache_meta.values():
            cache_type = meta.get('type', 'unknown')
            stats['by_type'][cache_type] = stats['by_type'].get(cache_type, 0) + 1
        
        # 캐시 크기 계산
        try:
            for meta in self.cache_meta.values():
                file_path = os.path.join(self.data_dir, meta['file'])
                if os.path.exists(file_path):
                    stats['cache_size_mb'] += os.path.getsize(file_path) / (1024 * 1024)
        except Exception as e:
            print(f"캐시 크기 계산 오류: {e}")
        
        return stats

# 전역 캐시 인스턴스
STOCK_CACHE = StockDataCache()
