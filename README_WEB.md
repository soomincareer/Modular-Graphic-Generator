# Module Grid Generator - Web Application

명암 차이로 형상을 만드는 그래픽 패턴 생성기의 웹 버전입니다.

## 기능

- **모듈 이미지 업로드**: 여러 모듈 이미지를 한 번에 업로드
- **모듈 미리보기**: 밝기 순으로 정렬된 모듈 이미지 미리보기
- **타겟 이미지 업로드**: 여러 타겟 이미지를 한 번에 처리
- **설정 가능**: Grid Size (예: 64x40), Output DPI (예: 600)
- **결과 확인**: total.md 파일을 웹에서 바로 확인
- **파일 다운로드**: total.md 파일 및 모든 결과 파일 ZIP 다운로드

## 설치 방법

1. 의존성 설치:
```bash
pip install -r requirements.txt
```

## 실행 방법

```bash
python web_app.py
```

서버가 시작되면 브라우저에서 `http://127.0.0.1:5000` 으로 접속하세요.

## ☁️ 컴퓨터를 켜두지 않고 배포하는 방법

로컬 PC를 하루 종일 켜둘 수 없다면, 아래처럼 **클라우드 서버에 상시 실행**하는 방식이 가장 현실적입니다.

### 1) Flask 앱을 GitHub 저장소에서 바로 배포 (Render 권장)

아래 순서대로 진행하면, 로컬 PC를 꺼도 웹사이트는 계속 동작합니다.

#### 1-1. GitHub 준비

1. GitHub에서 새 저장소를 만듭니다.
2. 현재 프로젝트를 푸시합니다.

```bash
git init
git add .
git commit -m "initial commit"
git branch -M main
git remote add origin https://github.com/<YOUR_ID>/<YOUR_REPO>.git
git push -u origin main
```

#### 1-2. Render에서 바로 배포

1. [Render](https://render.com) 로그인
2. **New + → Web Service** 클릭
3. GitHub 계정 연동 후 저장소 선택
4. 아래 값 입력
   - Runtime: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn web_app:app --bind 0.0.0.0:$PORT`
5. **Create Web Service** 클릭
6. 배포 완료 후 발급 URL 접속

#### 1-3. 저장소에 이미 포함된 배포 파일

- `requirements.txt`: 배포 시 설치할 Python 패키지 목록
- `Procfile`: PaaS 공통 시작 명령
- `render.yaml`: Render Blueprint 설정 파일

> 참고: Render 무료 플랜은 일정 시간 트래픽이 없으면 sleep 될 수 있습니다. 항상 켜진 상태가 필요하면 유료 플랜을 사용하세요.

### 2) VPS (EC2, Lightsail, Oracle Cloud 등)

`Nginx + Gunicorn + Flask` 조합으로 운영합니다.

장점:

- 자유도 높음 (파일 크기, 프로세스 개수, 디스크 정책)

단점:

- 서버 운영(보안 업데이트, 방화벽, SSL) 직접 관리 필요

### 3) Docker 기반 배포

Docker 이미지를 만들어 어디서든 동일하게 실행할 수 있습니다.

권장 시나리오:

- 개인 서버/클라우드/VPS로 이동 가능성이 큰 경우
- 추후 작업 큐(Celery)나 외부 스토리지(S3) 연동 계획이 있는 경우

### 운영 시 꼭 고려할 점

- 현재 앱은 임시 폴더에 결과물을 저장하므로 서버 재시작 시 파일이 유실될 수 있습니다.
- 장기 운영 시에는 S3 같은 외부 스토리지 사용을 권장합니다.
- 업로드 제한(`MAX_CONTENT_LENGTH=500MB`)이 크므로, 호스팅 플랜의 디스크/메모리 제한을 확인하세요.

## 사용 방법

1. **모듈 이미지 업로드**
   - "모듈 폴더" 섹션에서 여러 모듈 이미지를 선택합니다
   - 업로드 후 밝기 순으로 정렬된 미리보기가 표시됩니다

2. **타겟 이미지 업로드**
   - "타겟 이미지" 섹션에서 변환할 이미지를 선택합니다
   - 여러 이미지를 한 번에 선택할 수 있습니다

3. **설정**
   - Grid Size: 예) 64x40 (가로x세로)
   - Output DPI: 예) 600 (72~1200 범위)

4. **이미지 생성**
   - "이미지 생성" 버튼을 클릭합니다
   - 처리가 완료되면 total.md 내용이 표시됩니다

5. **결과 다운로드**
   - "total.md 다운로드": total.md 파일만 다운로드
   - "모든 결과 파일 다운로드 (ZIP)": 모든 결과 파일을 ZIP으로 다운로드

## 주요 특징

- **반응형 UI**: 아름다운 그라디언트 디자인
- **실시간 미리보기**: 모듈 이미지의 밝기 정보를 실시간으로 확인
- **일괄 처리**: 여러 타겟 이미지를 한 번에 처리
- **마크다운 렌더링**: total.md 파일을 웹에서 바로 확인

## 기술 스택

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript
- **Image Processing**: Pillow, NumPy
- **Markdown Rendering**: marked.js

## 파일 구조

```
PythonProject/
├── web_app.py              # Flask 웹 애플리케이션
├── module_grid_generator.py # 핵심 로직
├── requirements.txt         # Python 의존성
├── templates/
│   └── index.html          # 웹 인터페이스
└── README_WEB.md           # 이 문서
```

## 참고사항

- 최대 업로드 파일 크기: 500MB
- 지원 이미지 형식: PNG, JPG, JPEG, BMP, GIF, TIFF, WEBP
- 임시 파일은 시스템 임시 폴더에 저장됩니다
