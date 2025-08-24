# 🚀 S&P 400 주식 분석기 배포 가이드

## 1️⃣ Streamlit Cloud (가장 쉬운 방법) ⭐

### 장점
- ✅ **완전 무료**
- ✅ **GitHub 연동 자동 배포**
- ✅ **도메인 자동 제공**
- ✅ **설정 거의 불필요**

### 배포 방법
1. **GitHub 저장소 생성**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/stock-analyzer.git
   git push -u origin main
   ```

2. **Streamlit Cloud 접속**
   - https://share.streamlit.io/ 방문
   - GitHub 계정으로 로그인

3. **앱 배포**
   - "New app" 클릭
   - Repository: `YOUR_USERNAME/stock-analyzer`
   - Branch: `main`
   - Main file path: `stock_webapp.py`
   - "Deploy!" 클릭

4. **자동 배포 완료**
   - URL: `https://YOUR_USERNAME-stock-analyzer.streamlit.app/`

---

## 2️⃣ Heroku (안정적)

### 장점
- ✅ **신뢰성 높음**
- ✅ **커스텀 도메인 지원**
- ✅ **스케일링 가능**

### 배포 방법
1. **Heroku CLI 설치**
   ```bash
   # Windows
   winget install Heroku.CLI
   
   # macOS
   brew install heroku/brew/heroku
   ```

2. **Heroku 앱 생성**
   ```bash
   heroku create your-stock-analyzer
   git push heroku main
   ```

3. **환경 변수 설정**
   ```bash
   heroku config:set PYTHON_VERSION=3.9.19
   ```

---

## 3️⃣ Railway (현대적)

### 장점
- ✅ **GitHub 자동 배포**
- ✅ **현대적 UI**
- ✅ **쉬운 환경 변수 관리**

### 배포 방법
1. **Railway 방문**: https://railway.app/
2. **GitHub 연결 후 저장소 선택**
3. **자동 배포 완료**

---

## 4️⃣ Render (무료)

### 장점
- ✅ **무료 플랜 제공**
- ✅ **자동 SSL**
- ✅ **GitHub 연동**

### 배포 방법
1. **Render 방문**: https://render.com/
2. **"New Web Service" 선택**
3. **GitHub 저장소 연결**
4. **설정**:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `streamlit run stock_webapp.py --server.port=$PORT --server.address=0.0.0.0`

---

## 5️⃣ AWS EC2 (고급)

### 장점
- ✅ **완전한 제어권**
- ✅ **확장성**
- ✅ **커스터마이징 가능**

### 배포 방법
1. **EC2 인스턴스 생성**
2. **환경 설정**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip
   pip3 install -r requirements.txt
   ```
3. **서비스 실행**
   ```bash
   streamlit run stock_webapp.py --server.port=8501 --server.address=0.0.0.0
   ```

---

## 📋 배포 전 체크리스트

### 필수 파일들
- ✅ `stock_webapp.py` (메인 앱)
- ✅ `requirements.txt` (패키지 의존성)
- ✅ `.streamlit/config.toml` (설정)
- ✅ `Procfile` (Heroku용)
- ✅ `runtime.txt` (Python 버전)

### 환경 변수 (필요시)
```bash
PYTHON_VERSION=3.9.19
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_SERVER_PORT=8501
```

---

## 🔧 문제 해결

### 메모리 부족 시
```python
# stock_webapp.py 최상단에 추가
import os
os.environ['STREAMLIT_SERVER_MAX_UPLOAD_SIZE'] = '200'
```

### 타임아웃 문제 시
```toml
# .streamlit/config.toml에 추가
[server]
maxUploadSize = 200
```

---

## 🎯 추천 방법

### 빠른 테스트용
**Streamlit Cloud** - 5분만에 배포 가능

### 정식 서비스용
**Railway** 또는 **Render** - 안정적이고 무료

### 상업적 사용
**Heroku** 또는 **AWS** - 확장성과 안정성

---

## 📞 지원

배포 중 문제가 발생하면:
1. 로그 확인: `streamlit run stock_webapp.py --logger.level=debug`
2. 패키지 버전 확인: `pip list`
3. Python 버전 확인: `python --version`
