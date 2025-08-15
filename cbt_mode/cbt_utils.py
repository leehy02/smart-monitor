import re
from typing import List
from .cbt_config import FORBIDDEN, PLAN_START_TAG, PLAN_END_TAG


# ───────────────────────────────
# 1. 유저 발화만 추출
# ───────────────────────────────
def user_only_context(messages: List[dict]) -> str:
    """
    assistant/system 제외하고 user 발화만 이어붙여 분석
    """
    user_texts = [m["content"] for m in messages if m["role"] == "user"]
    return "\n".join(user_texts).strip() or "대화 없음"


# ───────────────────────────────
# 2. GPT 응답 클린업
# ───────────────────────────────
def sanitize_output(text: str, fallback: str = "없음") -> str:
    """
    - '예시 형식' 안내 줄 제거
    - 불용어(FORBIDDEN) 포함 시 fallback 반환
    - 양쪽 불필요한 따옴표, 공백 제거
    """
    clean = (text or "").strip()
    clean = re.sub(r"(예시\s*형식.*$)", "", clean,
                   flags=re.IGNORECASE | re.MULTILINE).strip()
    clean = clean.strip(' "\'')
    
    if any(w in clean for w in FORBIDDEN):
        return fallback
    return clean if clean else fallback


# ───────────────────────────────
# 3. 특정 태그 블록 추출
# ───────────────────────────────
def _extract_block(text: str, start_tag: str, end_tag: str) -> str:
    """
    텍스트에서 마지막 start_tag ~ end_tag 구간 추출
    """
    try:
        start = text.rfind(start_tag)
        end = text.rfind(end_tag)
        if start != -1 and end != -1 and end > start:
            return text[start + len(start_tag):end].strip()
    except Exception:
        pass
    return ""


# ───────────────────────────────
# 4. 대화 히스토리에서 PLAN 추출
# ───────────────────────────────
def extract_plan_from_history(messages: List[dict]) -> str:
    """
    assistant 메시지에서 [PLAN_START]...[PLAN_END] 가장 최근 블록 추출
    """
    for m in reversed(messages):
        if m["role"] != "assistant":
            continue
        block = _extract_block(m["content"], PLAN_START_TAG, PLAN_END_TAG)
        if block:
            return block
    return ""


# ───────────────────────────────
# 5. PLAN 태그 제거
# ───────────────────────────────
def strip_plan_tags(text: str) -> str:
    """
    [PLAN_START], [PLAN_END] 태그 제거
    """
    return re.sub(rf"{re.escape(PLAN_START_TAG)}|{re.escape(PLAN_END_TAG)}", "", text or "").strip()
