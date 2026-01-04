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
