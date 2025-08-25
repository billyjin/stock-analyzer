"""
국내/미국 주식 리스트 관리 시스템
소형주, 대형주, 테마주 등 체계적 분류 및 관리
"""

import json
import os
from typing import Dict, List, Set
from datetime import datetime

class StockListManager:
    """주식 리스트 관리 클래스"""
    
    def __init__(self, data_file: str = "stock_lists.json"):
        self.data_file = data_file
        self.stock_lists = self._load_stock_lists()
        
    def _load_stock_lists(self) -> Dict:
        """주식 리스트 데이터 로드"""
        default_lists = {
            "korean_stocks": {
                "large_cap": {
                    "IT_tech": {
                        "005930": "삼성전자", "000660": "SK하이닉스", "035420": "NAVER", 
                        "035720": "카카오", "018260": "삼성에스디에스"
                    },
                    "finance": {
                        "055550": "신한지주", "086790": "하나금융지주", "316140": "우리금융지주",
                        "138930": "BNK금융지주", "024110": "기업은행"
                    },
                    "auto": {
                        "005380": "현대차", "000270": "기아", "012330": "현대모비스"
                    },
                    "chemical": {
                        "051910": "LG화학", "009830": "한화솔루션", "011170": "롯데케미칼"
                    }
                },
                "small_cap": {
                    "IT_tech": {
                        "060310": "3S", "095570": "AJ네트웍스", "078340": "컴투스",
                        "052690": "한전기술", "036810": "에프텍", "053800": "마니커"
                    },
                    "bio": {
                        "207940": "삼성바이오", "068270": "셀트리온", "196170": "알테오젠",
                        "214450": "파마리서치", "145020": "휴젤", "326030": "SK바이오팜"
                    },
                    "game": {
                        "259960": "크래프톤", "194480": "데브시스터즈", "112040": "위메이드",
                        "078340": "컴투스", "053800": "마니커", "181710": "NHN"
                    }
                },
                "theme_stocks": {
                    "renewable_energy": {
                        "267250": "HD현대중공업", "010620": "현대미포조선", "079550": "LIG넥스원",
                        "051600": "한국선재", "336260": "두산에너빌리티"
                    },
                    "defense": {
                        "079550": "LIG넥스원", "047810": "한국항공우주", "272210": "한화시스템",
                        "064350": "현대로템", "218410": "RFHIC"
                    },
                    "semiconductor": {
                        "042700": "한미반도체", "039030": "이오테크닉스", "084370": "미코",
                        "067310": "하나마이크론", "131970": "두산테스나"
                    }
                },
                "speculation_candidates": {
                    "high_volatility": {
                        "033240": "자화전자", "018470": "삼화페인트", "095910": "JW신약",
                        "336260": "두산에너빌리티", "052690": "한전기술"
                    }
                }
            },
            "us_stocks": {
                "large_cap": {
                    "tech": {
                        "AAPL": "Apple Inc", "MSFT": "Microsoft", "GOOGL": "Alphabet",
                        "AMZN": "Amazon", "TSLA": "Tesla", "META": "Meta Platforms"
                    },
                    "finance": {
                        "JPM": "JPMorgan Chase", "BAC": "Bank of America", "WFC": "Wells Fargo",
                        "GS": "Goldman Sachs", "MS": "Morgan Stanley"
                    },
                    "consumer": {
                        "WMT": "Walmart", "PG": "Procter & Gamble", "KO": "Coca-Cola",
                        "PEP": "PepsiCo", "NKE": "Nike"
                    }
                },
                "small_cap": {
                    "biotech": {
                        "MRNA": "Moderna", "BNTX": "BioNTech", "NVAX": "Novavax",
                        "SRPT": "Sarepta Therapeutics", "BMRN": "BioMarin", "GILD": "Gilead Sciences",
                        "BIIB": "Biogen", "AMGN": "Amgen", "VRTX": "Vertex Pharmaceuticals"
                    },
                    "fintech": {
                        "SQ": "Block Inc", "PYPL": "PayPal", "COIN": "Coinbase",
                        "SOFI": "SoFi Technologies", "UPST": "Upstart", "AFRM": "Affirm",
                        "HOOD": "Robinhood", "LMND": "Lemonade"
                    },
                    "clean_energy": {
                        "ENPH": "Enphase Energy", "SEDG": "SolarEdge", "PLUG": "Plug Power",
                        "FSLR": "First Solar", "RUN": "Sunrun", "SPWR": "SunPower",
                        "NOVA": "Sunnova Energy", "CSIQ": "Canadian Solar"
                    },
                    "gaming": {
                        "RBLX": "Roblox", "DKNG": "DraftKings", "TTWO": "Take-Two Interactive",
                        "EA": "Electronic Arts", "ATVI": "Activision Blizzard", "ZNGA": "Zynga"
                    },
                    "ev_auto": {
                        "RIVN": "Rivian", "LCID": "Lucid Group", "NIO": "NIO Inc",
                        "XPEV": "XPeng", "LI": "Li Auto", "NKLA": "Nikola"
                    },
                    "ai_tech": {
                        "PLTR": "Palantir", "SNOW": "Snowflake", "CRWD": "CrowdStrike",
                        "ZM": "Zoom", "DOCU": "DocuSign", "OKTA": "Okta"
                    },
                    "meme_stocks": {
                        "GME": "GameStop", "AMC": "AMC Entertainment", "BB": "BlackBerry",
                        "NOK": "Nokia", "BBBY": "Bed Bath & Beyond", "EXPR": "Express"
                    },
                    "cannabis": {
                        "TLRY": "Tilray", "CGC": "Canopy Growth", "ACB": "Aurora Cannabis",
                        "CRON": "Cronos Group", "SNDL": "Sundial Growers"
                    },
                    "space": {
                        "SPCE": "Virgin Galactic", "ASTR": "Astra Space", "RKLB": "Rocket Lab",
                        "PL": "Planet Labs", "IRDM": "Iridium Communications"
                    },
                    "streaming": {
                        "ROKU": "Roku", "SPOT": "Spotify", "FUBO": "fuboTV",
                        "PARA": "Paramount Global", "WBD": "Warner Bros Discovery"
                    }
                },
                "speculation_candidates": {
                    "penny_stocks": {
                        "SNDL": "Sundial Growers", "GNUS": "Genius Brands", "BNGO": "Bionano Genomics",
                        "PROG": "Progenity", "MVIS": "MicroVision", "CLOV": "Clover Health"
                    },
                    "high_volatility": {
                        "DWAC": "Digital World Acquisition", "PHUN": "Phunware", "MARK": "Remark Holdings",
                        "BBIG": "Vinco Ventures", "SPRT": "Support.com", "IRNT": "IronNet"
                    },
                    "reddit_favorites": {
                        "GME": "GameStop", "AMC": "AMC Entertainment", "PLTR": "Palantir",
                        "WISH": "ContextLogic", "CLOV": "Clover Health", "SOFI": "SoFi Technologies"
                    }
                },
                "grain_commodity": {
                    "agriculture": {
                        "ADM": "Archer Daniels Midland", "BG": "Bunge", "DE": "Deere & Company",
                        "CTVA": "Corteva", "CF": "CF Industries"
                    },
                    "food": {
                        "GIS": "General Mills", "K": "Kellogg", "TSN": "Tyson Foods",
                        "CAG": "ConAgra Foods", "CPB": "Campbell Soup"
                    }
                }
            },
            "metadata": {
                "last_updated": datetime.now().isoformat(),
                "version": "1.0"
            }
        }
        
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"주식 리스트 로드 오류: {e}")
        
        return default_lists
    
    def save_stock_lists(self):
        """주식 리스트 저장"""
        try:
            self.stock_lists["metadata"]["last_updated"] = datetime.now().isoformat()
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.stock_lists, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"주식 리스트 저장 오류: {e}")
    
    def get_korean_stocks(self, category: str = None, subcategory: str = None) -> Dict[str, any]:
        """한국 주식 리스트 조회 (카테고리 정보 포함)"""
        korean_stocks = self.stock_lists.get("korean_stocks", {})
        
        if category is None:
            # 모든 한국 주식 반환 (카테고리 정보 포함)
            result = {}
            for cat_name, cat_data in korean_stocks.items():
                if isinstance(cat_data, dict):
                    for subcat_name, subcat_data in cat_data.items():
                        if isinstance(subcat_data, dict):
                            for symbol, name in subcat_data.items():
                                result[symbol] = {
                                    'name': name,
                                    'category': cat_name,
                                    'subcategory': subcat_name
                                }
            return result
        
        if category in korean_stocks:
            if subcategory is None:
                # 카테고리 내 모든 주식 반환
                result = {}
                cat_data = korean_stocks[category]
                for subcat_name, subcat_data in cat_data.items():
                    if isinstance(subcat_data, dict):
                        for symbol, name in subcat_data.items():
                            result[symbol] = {
                                'name': name,
                                'category': category,
                                'subcategory': subcat_name
                            }
                return result
            else:
                # 특정 서브카테고리 반환
                result = {}
                subcat_data = korean_stocks[category].get(subcategory, {})
                for symbol, name in subcat_data.items():
                    result[symbol] = {
                        'name': name,
                        'category': category,
                        'subcategory': subcategory
                    }
                return result
        
        return {}
    
    def get_us_stocks(self, category: str = None, subcategory: str = None) -> Dict[str, any]:
        """미국 주식 리스트 조회 (카테고리 정보 포함)"""
        us_stocks = self.stock_lists.get("us_stocks", {})
        
        if category is None:
            # 모든 미국 주식 반환 (카테고리 정보 포함)
            result = {}
            for cat_name, cat_data in us_stocks.items():
                if isinstance(cat_data, dict):
                    for subcat_name, subcat_data in cat_data.items():
                        if isinstance(subcat_data, dict):
                            for symbol, name in subcat_data.items():
                                result[symbol] = {
                                    'name': name,
                                    'category': cat_name,
                                    'subcategory': subcat_name
                                }
            return result
        
        if category in us_stocks:
            if subcategory is None:
                # 카테고리 내 모든 주식 반환
                result = {}
                cat_data = us_stocks[category]
                for subcat_name, subcat_data in cat_data.items():
                    if isinstance(subcat_data, dict):
                        for symbol, name in subcat_data.items():
                            result[symbol] = {
                                'name': name,
                                'category': category,
                                'subcategory': subcat_name
                            }
                return result
            else:
                # 특정 서브카테고리 반환
                result = {}
                subcat_data = us_stocks[category].get(subcategory, {})
                for symbol, name in subcat_data.items():
                    result[symbol] = {
                        'name': name,
                        'category': category,
                        'subcategory': subcategory
                    }
                return result
        
        return {}
    
    def get_small_cap_stocks(self, market: str = "korean") -> Dict[str, str]:
        """소형주 리스트 조회"""
        if market == "korean":
            return self.get_korean_stocks("small_cap")
        elif market == "us":
            return self.get_us_stocks("small_cap")
        else:
            # 전체 소형주
            korean_small = self.get_korean_stocks("small_cap")
            us_small = self.get_us_stocks("small_cap")
            korean_small.update(us_small)
            return korean_small
    
    def get_speculation_candidates(self) -> Dict[str, str]:
        """잡주 후보 리스트 조회"""
        korean_spec = self.get_korean_stocks("speculation_candidates")
        korean_theme = self.get_korean_stocks("theme_stocks")
        korean_small = self.get_korean_stocks("small_cap")
        
        # 합치기
        result = {}
        result.update(korean_spec)
        result.update(korean_theme)
        result.update(korean_small)
        
        return result
    
    def add_stock(self, market: str, category: str, subcategory: str, symbol: str, name: str):
        """주식 추가"""
        if market not in self.stock_lists:
            self.stock_lists[market] = {}
        
        if category not in self.stock_lists[market]:
            self.stock_lists[market][category] = {}
        
        if subcategory not in self.stock_lists[market][category]:
            self.stock_lists[market][category][subcategory] = {}
        
        self.stock_lists[market][category][subcategory][symbol] = name
        self.save_stock_lists()
    
    def remove_stock(self, market: str, category: str, subcategory: str, symbol: str):
        """주식 제거"""
        try:
            if (market in self.stock_lists and 
                category in self.stock_lists[market] and 
                subcategory in self.stock_lists[market][category] and 
                symbol in self.stock_lists[market][category][subcategory]):
                
                del self.stock_lists[market][category][subcategory][symbol]
                self.save_stock_lists()
                return True
        except Exception as e:
            print(f"주식 제거 오류: {e}")
        
        return False
    
    def find_stock_info(self, symbol: str) -> Dict:
        """주식 정보 찾기"""
        for market, market_data in self.stock_lists.items():
            if market == "metadata":
                continue
                
            for category, cat_data in market_data.items():
                for subcategory, stocks in cat_data.items():
                    if symbol in stocks:
                        return {
                            "symbol": symbol,
                            "name": stocks[symbol],
                            "market": market,
                            "category": category,
                            "subcategory": subcategory
                        }
        
        return {}
    
    def get_categories(self, market: str) -> List[str]:
        """특정 시장의 카테고리 목록"""
        if market in self.stock_lists:
            return list(self.stock_lists[market].keys())
        return []
    
    def get_subcategories(self, market: str, category: str) -> List[str]:
        """특정 카테고리의 서브카테고리 목록"""
        if market in self.stock_lists and category in self.stock_lists[market]:
            return list(self.stock_lists[market][category].keys())
        return []
    
    def get_stats(self) -> Dict:
        """주식 리스트 통계"""
        stats = {
            "total_stocks": 0,
            "by_market": {},
            "by_category": {}
        }
        
        for market, market_data in self.stock_lists.items():
            if market == "metadata":
                continue
                
            market_count = 0
            stats["by_market"][market] = {}
            
            for category, cat_data in market_data.items():
                cat_count = 0
                stats["by_market"][market][category] = {}
                
                for subcategory, stocks in cat_data.items():
                    stock_count = len(stocks)
                    cat_count += stock_count
                    stats["by_market"][market][category][subcategory] = stock_count
                
                market_count += cat_count
                if category not in stats["by_category"]:
                    stats["by_category"][category] = 0
                stats["by_category"][category] += cat_count
            
            stats["total_stocks"] += market_count
        
        return stats

# 전역 주식 리스트 관리자
STOCK_LIST_MANAGER = StockListManager()
