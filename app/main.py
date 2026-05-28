from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import chat, settings, user
from .database import init_db

app = FastAPI(title="신입사원 교육 챗봇 API")


@app.on_event("startup")
def on_startup():
    init_db()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(user.router)
app.include_router(settings.router)


@app.get("/")
async def root():
    return {"message": "신입사원 교육 챗봇 API 서버가 실행 중입니다."}


@app.get("/api/chat/topics")
async def get_topics():
    return [
        {"id": "mail", "name": "메일쓰기"},
        {"id": "comm", "name": "커뮤니케이션"},
        {"id": "org", "name": "조직 적응"},
        {"id": "collab", "name": "협업/태도"},
    ]
