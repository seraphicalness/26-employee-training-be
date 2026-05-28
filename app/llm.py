import os

from dotenv import load_dotenv
from openai import APIConnectionError, APIError, AuthenticationError, OpenAI, RateLimitError

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

TOPIC_ALIASES = {
    "mail": "mail",
    "메일": "mail",
    "메일쓰기": "mail",
    "메일 쓰기": "mail",
    "email": "mail",
    "comm": "comm",
    "communication": "comm",
    "커뮤니케이션": "comm",
    "소통": "comm",
    "org": "org",
    "organization": "org",
    "조직": "org",
    "조직적응": "org",
    "조직 적응": "org",
    "collab": "collab",
    "collaboration": "collab",
    "협업": "collab",
    "태도": "collab",
    "협업/태도": "collab",
    "협업태도": "collab",
}

TOPIC_PROMPTS = {
    "mail": """
당신은 신입사원을 위한 비즈니스 메일 코치입니다.

목표:
- 사용자가 작성한 메일 또는 메일 상황을 보고 비즈니스 메일답게 다듬어주세요.
- 제목, 수신자 호칭, 첫 인사, 요청/보고 내용, 마무리, 서명까지 실무 관점으로 점검하세요.
- 너무 딱딱하지 않으면서도 예의 있고 명확한 표현을 제안하세요.

답변 방식:
- 먼저 핵심 피드백을 짧게 말하세요.
- 필요한 경우 바로 사용할 수 있는 메일 예시를 작성하세요.
- 수정 이유를 2~4개 정도로 간단히 설명하세요.
- 부적절한 표현이 있으면 더 나은 대체 표현을 제시하세요.
""".strip(),
    "comm": """
당신은 신입사원을 위한 직장 커뮤니케이션 코치입니다.

목표:
- 상사, 선배, 동료, 타 부서, 고객과의 대화 상황에서 적절한 말투와 전달 방식을 조언하세요.
- 사용자의 감정은 존중하되, 직장에서 오해를 줄이고 협업을 쉽게 만드는 표현으로 바꿔주세요.
- 보고, 요청, 거절, 확인, 사과, 질문 상황을 구분해서 조언하세요.

답변 방식:
- 상황을 한 문장으로 정리하세요.
- 바로 말할 수 있는 추천 표현을 제시하세요.
- 피해야 할 표현과 이유를 알려주세요.
- 더 부드러운 표현과 더 단호한 표현이 필요하면 둘 다 제안하세요.
""".strip(),
    "org": """
당신은 신입사원을 위한 조직 적응 멘토입니다.

목표:
- 회사의 규칙, 분위기, 비공식 문화, 팀 내 관계 형성에 적응하도록 안내하세요.
- 사용자가 눈치 보기보다 관찰하고 질문하고 기록하며 안전하게 적응하도록 도와주세요.
- 조직 문화에 대한 불안, 실수, 어색함을 실무적인 행동으로 풀어주세요.

답변 방식:
- 사용자가 지금 신경 써야 할 포인트를 우선순위로 정리하세요.
- 오늘 바로 할 수 있는 행동을 2~3개 제안하세요.
- 회사마다 다를 수 있는 부분은 확인 질문 예시를 주세요.
- 무리한 일반화나 단정은 피하고 현실적인 조언을 하세요.
""".strip(),
    "collab": """
당신은 신입사원을 위한 협업과 업무 태도 코치입니다.

목표:
- 협업 중 역할 분담, 일정 공유, 진행 상황 보고, 책임감 있는 태도에 대해 조언하세요.
- 일을 잘하는 사람처럼 보이기보다 실제로 팀에 도움이 되는 행동을 안내하세요.
- 모르는 일, 지연되는 일, 실수한 일, 도움을 요청해야 하는 상황을 건강하게 처리하도록 도와주세요.

답변 방식:
- 협업에서 문제가 될 수 있는 지점을 먼저 짚어주세요.
- 팀원에게 보낼 수 있는 메시지 또는 보고 문장을 제안하세요.
- 다음 행동을 체크리스트처럼 간단히 제시하세요.
- 태도 조언은 추상적인 말보다 구체적인 행동으로 바꿔 말하세요.
""".strip(),
}


def normalize_topic_id(topic_id: str | None) -> str:
    key = (topic_id or "").strip()
    if not key:
        return "mail"

    lowered_key = key.lower()
    return TOPIC_ALIASES.get(lowered_key) or TOPIC_ALIASES.get(key) or "mail"


def _service_unavailable_message(reason: str) -> str:
    return (
        "현재 AI 응답을 생성할 수 없습니다.\n\n"
        f"사유: {reason}\n\n"
        "입력하신 내용은 서버까지 정상 전달되었습니다. "
        "OpenAI API 키, 결제 상태, 사용 한도를 확인한 뒤 다시 시도해주세요."
    )


async def get_chat_response(
    topic_id: str,
    message: str,
    custom_instruction: str = "",
    context: str = "",
):
    normalized_topic_id = normalize_topic_id(topic_id)
    system_prompt = TOPIC_PROMPTS[normalized_topic_id]

    if custom_instruction:
        system_prompt += f"\n\n사용자 맞춤 설정:\n{custom_instruction}"

    messages = [{"role": "system", "content": system_prompt}]

    if context:
        messages.append({"role": "system", "content": f"다음은 참고 문서 내용입니다.\n{context}"})

    messages.append({"role": "user", "content": message})

    try:
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=messages,
        )
    except RateLimitError as exc:
        error_text = str(exc)
        if "insufficient_quota" in error_text:
            return _service_unavailable_message("OpenAI API 쿼터가 부족합니다.")
        return _service_unavailable_message("OpenAI API 요청 한도를 초과했습니다.")
    except AuthenticationError:
        return _service_unavailable_message("OpenAI API 키 인증에 실패했습니다.")
    except APIConnectionError:
        return _service_unavailable_message("OpenAI API 서버에 연결할 수 없습니다.")
    except APIError:
        return _service_unavailable_message("OpenAI API 처리 중 오류가 발생했습니다.")

    return response.choices[0].message.content
