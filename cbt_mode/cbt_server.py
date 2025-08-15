from flask import Blueprint, request, render_template, make_response
from data_save.t_data import save_summary_to_db
import json

# 프롬프트/초기메시지
from .cbt_prompts import (
    initial_messages,
    EVENT_PROMPT, EMOTION_PROMPT, AUTO_PROMPT,
    ALTERNATIVE_PROMPT, PLAN_PROMPT, GOAL_PROMPT,
    DISTORTION_JSON_PROMPT, ALLOWED_DISTORTIONS,
)

# 구성/도구
from .cbt_config import MODEL, client  # MODEL은 참고용
from .cbt_services import llm_call, analyze_distortions_from_autos
from .cbt_utils import user_only_context, extract_plan_from_history, strip_plan_tags

cbt_server = Blueprint("cbt_server", __name__)

def format_distortion_sentence(dist_map: dict) -> str:
    if not dist_map:
        return "주요 인지 왜곡 패턴은 확인되지 않았습니다."
    items = [(k, v) for k, v in dist_map.items() if isinstance(v, int) and v > 0]
    if not items:
        return "주요 인지 왜곡 패턴은 확인되지 않았습니다."
    items.sort(key=lambda x: (-x[1], x[0]))
    names = [k for k, _ in items]
    listed = ", ".join(names) if len(names) > 1 else names[0]
    return f"주로 {listed} 패턴이 나타났습니다."

# ===== 전역 상태 (데모/단일 사용자 기준) =====
messages = initial_messages()
event_result = ""
emotion_result = ""
distortion_result = ""  # 화면 표시에 쓰는 문자열 버전
auto_result = ""
alternative_result = ""
plan_result = ""
goal_result = ""

@cbt_server.after_request
def add_no_cache_headers(resp):
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp

@cbt_server.route("/", methods=["GET", "POST"])
def index():
    global messages, event_result, emotion_result, distortion_result
    global auto_result, alternative_result, plan_result, goal_result

    if request.method == "GET":
        # 초기화
        messages = initial_messages()
        event_result = emotion_result = distortion_result = ""
        auto_result = alternative_result = plan_result = goal_result = ""

        # ✅ 화면에 보일 히스토리는 태그 숨겨서 렌더
        history = [(m["role"], strip_plan_tags(m["content"])) for m in messages if m["role"] in ("user", "assistant")]
        return make_response(render_template(
            "index.html",
            event=None, emotion=None, distortion=None,
            auto=None, alternative=None, plan=None, goal=None,
            history=history, reset_on_refresh=False,
        ))

    # ---------- POST (대화 진행) ----------
    user_input = request.form.get("user_input", "").strip()
    is_command = user_input in ("종료", "중단")

    if user_input and not is_command:
        messages.append({"role": "user", "content": user_input})

    if is_command:
        # 사용자 발화만 모아 분석
        context_text = user_only_context(messages)

        # 1) 추출 계열
        event_result = llm_call(EVENT_PROMPT, context_text)
        emotion_result = llm_call(EMOTION_PROMPT, context_text)
        auto_result = llm_call(AUTO_PROMPT, context_text)

        # 2) 인지왜곡 집계 (필요 시 화면 표시 문자열 구성)
        distortion_map = analyze_distortions_from_autos(
            auto_result, ALLOWED_DISTORTIONS, DISTORTION_JSON_PROMPT
        )
        distortion_result = format_distortion_sentence(distortion_map)

        # 3) 생성 계열
        alternative_result = llm_call(ALTERNATIVE_PROMPT, context_text)
        goal_result = llm_call(GOAL_PROMPT, context_text)

        # 4) 실천 계획 — 상담 중 말한 그대로 우선 사용, 없으면 PLAN_PROMPT 폴백
        plan_from_chat = extract_plan_from_history(messages)  # ← 태그 포함 messages에서 추출
        if plan_from_chat:
            plan_result = plan_from_chat  # 번호/줄바꿈 유지
        else:
            tmp = llm_call(PLAN_PROMPT, context_text)
            if tmp and tmp != "없음":
                items = [s.strip() for s in tmp.split(",") if s.strip()]
                plan_result = "\n".join(f"{i+1}. {s}" for i, s in enumerate(items[:4]))
            else:
                plan_result = "없음"

        # ✅ 사용자 표시/저장 전에만 PLAN 태그 제거
        plan_result = strip_plan_tags(plan_result)

        # 저장 or 미저장 안내
        if user_input == "종료":
            try:
                save_summary_to_db(
                    event_text=event_result or "",
                    emotion_text=emotion_result or "",
                    auto_text=auto_result or "",
                    distortion_json=json.dumps(distortion_map, ensure_ascii=False),
                    alternative_text=alternative_result or "",
                    plan_text=plan_result or "",
                    goal_text=goal_result or "",
                )
            except Exception as e:
                print(f"[WARN] save_summary_to_db failed: {e}")

        end_msg = (
            "✅ 상담 종료. 금일 상담 내역이 성공적으로 저장되었어요! 아래에서 요약과 분석 내용을 확인해주세요. 앱에서는 더 자세한 내용을 조회할 수 있어요😊 "
            if user_input == "종료"
            else "✔️ 상담 중단. 이번 상담 내역은 따로 저장되지 않아요! 아래에서 현재까지 진행한 요약과 분석 내용을 확인해주세요😊"
        )
        messages.append({"role": "assistant", "content": end_msg})

    else:
        # 일반 대화: 원본을 messages에 저장(태그 포함) → 히스토리 렌더링에서만 숨김
        chat_response = client.chat.completions.create(
            model=MODEL, temperature=0.4, messages=messages
        ).choices[0].message.content
        # ❌ 여기서 strip_plan_tags() 하지 마세요 (히스토리 추출에 필요)
        messages.append({"role": "assistant", "content": chat_response})

    # ✅ 화면용 히스토리: 항상 태그 숨김
    history = [(m["role"], strip_plan_tags(m["content"])) for m in messages if m["role"] in ("user", "assistant")]

    return make_response(render_template(
        "index.html",
        event=event_result or None,
        emotion=emotion_result or None,
        distortion=distortion_result or None,
        auto=auto_result or None,
        alternative=alternative_result or None,
        plan=plan_result or None,     # 줄바꿈/번호 유지
        goal=goal_result or None,
        history=history,
        reset_on_refresh=True,
    ))
