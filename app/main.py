from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import chat, user, settings

app = FastAPI(title="신입사원 교육 챗봇 API")

# CORS 설정 (프론트엔드 연동용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 배포 시에는 특정 도메인만 허용하도록 수정 필요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(chat.router)
app.include_router(user.router)
app.include_router(settings.router)

@app.get("/")
async def root():
    return {"message": "신입사원 교육 챗봇 API 서버가 가동 중입니다."}

@app.get("/api/chat/topics")
async def get_topics():
    return [
        {"id": "mail", "name": "메일 쓰기"},
        {"id": "comm", "name": "커뮤니케이션"},
        {"id": "org", "name": "조직 적응"},
        {"id": "collab", "name": "협업/태도"}
    ]
