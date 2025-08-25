# 📱 S&P 400 주식 분석기 안드로이드 앱

## 🚀 설치 가이드

### 1. Android Studio 설정

1. **새 프로젝트 생성**
   - Android Studio 열기
   - "Create New Project" 선택
   - "Empty Activity" 템플릿 선택
   - Project name: `StockAnalyzer`
   - Package name: `com.stockanalyzer.app`
   - Language: `Java`
   - Minimum SDK: `API 24`

### 2. 파일 복사

제공된 파일들을 다음 위치에 복사하세요:

```
app/
├── src/main/
│   ├── AndroidManifest.xml
│   ├── java/com/stockanalyzer/app/
│   │   └── MainActivity.java
│   └── res/
│       ├── layout/
│       │   └── activity_main.xml
│       ├── values/
│       │   ├── strings.xml
│       │   └── themes.xml
│       └── drawable/
│           └── (아이콘 파일들)
└── build.gradle
```

### 3. Streamlit URL 설정

**중요**: `MainActivity.java`에서 다음 라인을 수정하세요:

```java
private static final String STREAMLIT_URL = "https://your-app-name.streamlit.app";
```

실제 Streamlit Cloud 배포 URL로 변경하세요.

### 4. 권한 확인

`AndroidManifest.xml`에서 다음 권한이 있는지 확인:
- `INTERNET`
- `ACCESS_NETWORK_STATE`

### 5. 빌드 및 실행

1. **Sync Project**: `File > Sync Project with Gradle Files`
2. **Clean Build**: `Build > Clean Project`
3. **Rebuild**: `Build > Rebuild Project`
4. **Run**: `Run > Run 'app'`

## 🎨 커스터마이징

### 앱 아이콘 변경
- `res/mipmap/` 폴더에 새 아이콘 추가
- 다양한 해상도별 아이콘 준비 (hdpi, mdpi, xhdpi, xxhdpi, xxxhdpi)

### 테마 색상 변경
`themes.xml`에서 다음 색상 수정:
- `colorPrimary`: 주 색상 (#2E7D32 - 녹색)
- `colorSecondary`: 보조 색상 (#4CAF50 - 연녹색)

### 로딩 메시지 변경
`strings.xml`에서 텍스트 수정 가능

## 🔧 문제 해결

### 일반적인 문제

1. **WebView 로딩 실패**
   - 인터넷 권한 확인
   - Streamlit URL이 올바른지 확인
   - HTTPS 사용 권장

2. **JavaScript 오류**
   - `WebSettings.setJavaScriptEnabled(true)` 확인
   - DOM Storage 활성화 확인

3. **네트워크 오류**
   - `usesCleartextTraffic="true"` 설정 확인
   - 네트워크 보안 정책 확인

### 디버깅

Chrome DevTools를 사용해 WebView 디버깅:
1. 앱 실행
2. Chrome에서 `chrome://inspect` 접속
3. WebView 선택하여 디버깅

## 📦 배포

### Debug APK 생성
```bash
./gradlew assembleDebug
```

### Release APK 생성
1. 키스토어 생성
2. `build.gradle`에서 signing 설정
3. ```bash
   ./gradlew assembleRelease
   ```

### Google Play Store 업로드
1. App Bundle 생성: `./gradlew bundleRelease`
2. Google Play Console에 업로드
3. 스토어 리스팅 작성

## 🌟 기능

- ✅ Streamlit 웹앱 완전 래핑
- ✅ 네트워크 오류 처리
- ✅ 로딩 화면
- ✅ 뒤로가기 버튼 지원
- ✅ 확대/축소 지원
- ✅ 오프라인 감지

## 📱 테스트된 환경

- Android 7.0+ (API 24+)
- Chrome WebView 최신 버전
- 4G/WiFi 연결
