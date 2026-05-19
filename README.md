# 신입사원 교육 챗봇 Backend (FastAPI)

## 실행 방법
1. 필요한 패키지 설치:
   ```bash
   pip install -r requirements.txt
   ```
2. `.env` 파일 설정:
   `OPENAI_API_KEY`를 실제 키로 수정하세요.

3. 서버 실행:
   ```bash
   uvicorn app.main:app --reload
   ```

## 주요 API 엔드포인트
- `POST /api/chat/upload`: 파일 업로드 (PDF, Docx 지원)
- `POST /api/chat/send`: 메시지 전송 및 GPT-4o 피드백 수신
- `GET /api/user/me`: 마이페이지 정보 조회
- `PUT /api/settings/prompt`: 맞춤형 프롬프트 설정
