# IZOF 멘탈 분석기

IZOF(Individual Zones of Optimal Functioning) 이론을 바탕으로 선수의 멘탈 상태를 분석하고 맞춤형 훈련법을 제안하는 Streamlit 웹 애플리케이션입니다.

## 주요 기능

- IZOF 검사 결과 데이터 분석
- Gemini AI를 활용한 개인별 맞춤형 멘탈 분석
- 훈련 요구량 시각화 (Plotly 차트)
- 요약 및 상세 분석 리포트 생성

## 로컬 실행

### 1. 환경 설정

```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.template .env
# .env 파일을 열어 GEMINI_API_KEY 설정
```

### 2. 애플리케이션 실행

```bash
streamlit run izof-app.py
```

## Docker 배포

### 1. 이미지 빌드

```bash
docker build -t izof-app .
```

### 2. 컨테이너 실행

```bash
# 환경 변수 파일 사용
docker run -p 8501:8501 --env-file .env izof-app

# 또는 직접 환경 변수 전달
docker run -p 8501:8501 -e GEMINI_API_KEY=your_api_key_here izof-app
```

### 3. Docker Compose (권장)

```yaml
version: '3.8'
services:
  izof-app:
    build: .
    ports:
      - "8501:8501"
    env_file:
      - .env
    restart: unless-stopped
```

```bash
docker-compose up -d
```

## 환경 변수

| 변수명 | 설명 | 필수 여부 |
|--------|------|-----------|
| `GEMINI_API_KEY` | Google Gemini API 키 | 필수 |
| `APP_DEBUG` | 디버그 모드 (기본값: false) | 선택 |

## API 키 설정

1. [Google AI Studio](https://makersuite.google.com/app/apikey)에서 Gemini API 키 발급
2. `.env` 파일에 키 추가 또는 환경 변수로 설정
3. **주의**: API 키는 절대 코드에 하드코딩하지 마세요

## 보안 고려사항

- `.env` 파일은 `.gitignore`에 포함되어 git에 추적되지 않습니다
- Docker 컨테이너는 non-root 사용자로 실행됩니다
- 프로덕션 환경에서는 HTTPS 사용을 권장합니다

## 프로덕션 배포 체크리스트

- [ ] API 키를 환경 변수 또는 시크릿 매니저로 관리
- [ ] HTTPS 설정 (리버스 프록시 또는 로드 밸런서)
- [ ] 리소스 제한 설정 (Docker memory/CPU limits)
- [ ] 모니터링 및 로깅 설정
- [ ] 헬스 체크 엔드포인트 활용
- [ ] 백업 및 재해 복구 계획

## 문제 해결

### 일반적인 오류

1. **API 키 오류**: `GEMINI_API_KEY` 환경 변수가 설정되었는지 확인
2. **포트 충돌**: 8501 포트가 이미 사용 중인 경우 다른 포트 사용
3. **의존성 오류**: `pip install -r requirements.txt` 재실행

### 로그 확인

```bash
# Docker 컨테이너 로그
docker logs <container_id>

# 실시간 로그 모니터링
docker logs -f <container_id>
```