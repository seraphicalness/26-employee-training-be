import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

TOPIC_PROMPTS = {
    "mail": "당신은 비즈니스 메일 작성 전문가입니다. 신입사원이 작성한 메일 초안을 분석하여, 비즈니스 에티켓(제목, 인사, 본문, 맺음말)에 맞는지 검토하고 더 나은 표현을 제안하세요.",
    "comm": "당신은 직장 내 커뮤니케이션 전문가입니다. 상사나 동료와의 대화 상황에서 신입사원이 어떻게 말하는 것이 좋을지, 예절과 효율성을 고려하여 조언하세요.",
    "org": "당신은 조직 문화 및 적응 전문가입니다. 신입사원이 회사의 규칙, 분위기, 비공식적인 문화에 잘 적응할 수 있도록 가이드를 제공하세요.",
    "collab": "당신은 협업 및 업무 태도 전문가입니다. 팀 프로젝트나 공동 작업 시 필요한 태도, 책임감, 그리고 효과적인 협업 방식에 대해 조언하세요."
}

async def get_chat_response(topic_id: str, message: str, custom_instruction: str = "", context: str = ""):
    system_prompt = TOPIC_PROMPTS.get(topic_id, "당신은 신입사원 교육 챗봇입니다.")
    
    if custom_instruction:
        system_prompt += f"\n\n사용자 맞춤 설정: {custom_instruction}"
    
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    if context:
        messages.append({"role": "system", "content": f"다음은 참고할 문서 내용입니다:\n{context}"})
    
    messages.append({"role": "user", "content": message})
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )
    
    return response.choices[0].message.content
