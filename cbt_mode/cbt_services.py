import json
from .cbt_config import MODEL, TEMPERATURE, client
from .cbt_utils import sanitize_output

def llm_call(system_prompt: str, context_text: str) -> str:
    """공통 LLM 콜 + 후처리(1회 보정 재시도 포함)"""
    out = client.chat.completions.create(
        model=MODEL, temperature=TEMPERATURE,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": context_text},
        ],
    ).choices[0].message.content
    s = sanitize_output(out)
    if s == "없음":
        retry_sys = system_prompt + "\n추가 규칙: 예시 형식을 복사하지 말고, 실제 대화에서 근거를 찾아 간결하게 출력하세요."
        out2 = client.chat.completions.create(
            model=MODEL, temperature=TEMPERATURE,
            messages=[
                {"role": "system", "content": retry_sys},
                {"role": "user", "content": context_text},
            ],
        ).choices[0].message.content
        s = sanitize_output(out2, fallback="없음")
    return s

def llm_call_json(system_prompt: str, user_payload: str) -> dict:
    """JSON만 받는 콜 (1회 보정 재시도)"""
    out = client.chat.completions.create(
        model=MODEL, temperature=TEMPERATURE,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_payload},
        ],
    ).choices[0].message.content
    try:
        return json.loads(out)
    except Exception:
        retry_sys = system_prompt + "\n추가 규칙: 설명 없이 JSON만 출력하세요."
        out2 = client.chat.completions.create(
            model=MODEL, temperature=TEMPERATURE,
            messages=[
                {"role": "system", "content": retry_sys},
                {"role": "user", "content": user_payload},
            ],
        ).choices[0].message.content
        return json.loads(out2)

def analyze_distortions_from_autos(auto_text: str, allowed_keys: list, distortion_json_prompt: str) -> dict:
    """
    auto_text: "나는 실패자야, 모두가 날 싫어해" 같은 쉼표 구분 문자열
    """
    autos = [s.strip() for s in (auto_text or "").split(",") if s.strip()]
    if not autos:
        return {}
    payload = json.dumps({"automatic_thoughts": autos}, ensure_ascii=False)
    result = llm_call_json(distortion_json_prompt, payload)
    cleaned = {
        k: int(v) for k, v in (result or {}).items()
        if k in allowed_keys and isinstance(v, (int, float)) and int(v) > 0
    }
    return cleaned
