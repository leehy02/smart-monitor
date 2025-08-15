import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# 모델/온도
MODEL = "gpt-4o"
TEMPERATURE = 0.2

# 과도 필터링 방지: '예시'는 제외
FORBIDDEN = {"종료", "중단", "저장", "안내", "출력 예시"}

# OpenAI 클라이언트 (공유)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 상담 중 표시용 태그 (사용자에게는 숨김)
PLAN_START_TAG = "[PLAN_START]"
PLAN_END_TAG   = "[PLAN_END]"
