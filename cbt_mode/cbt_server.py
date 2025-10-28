from flask import Blueprint, request, render_template, make_response
from data_save.t_data import save_sessions, save_summary_report, save_users, save_plans, save_emotions, save_thoughts, save_distortions
import json

# 프롬프트/초기메시지
from .cbt_prompts import (
    initial_messages,
    EVENT_PROMPT, EMOTION_PROMPT, AUTO_PROMPT,
    ALTERNATIVE_PROMPT, PLAN_PROMPT, GOAL_PROMPT,
    DISTORTION_JSON_PROMPT, ALLOWED_DISTORTIONS,
    EMOTION_JSON_PROMPT, USER_PROMPT
)

# 구성/도구
from .cbt_config import MODEL, client  # MODEL은 참고용
from .cbt_services import llm_call, llm_call_json, analyze_distortions_from_autos
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

# ===== 2단계 저장 데이터 목록 =====
user_name = ""
user_age = 0
user_gender = ""

# ===== 4단계 저장 데이터 목록 =====
messages = initial_messages()
background = ""
emotion_change = ""
cognitive_distortion_summary = ""  # 화면 표시에 쓰는 문자열 버전
automatic_thought = ""
alternative_thought = ""
plan_recommendation = ""
improvement_goal = ""

# ===== 5단계 저장 데이터 목록 =====
emotion_name = []
emotion_score = []
division = []
# 감정 분석 결과는 4단계 데이터 활용하기

# ===== 6단계 저장 데이터 목록 =====
distortion_name = []
count = []
# automatic_thought = 4단계 데이터 재사용
automatic_analysis = ""
# alternative_thought = 4단계 데이터 재사용
alternative_analysis= ""

# ===== 7단계 저장 데이터 목록 =====
plan_text_list = []

@cbt_server.after_request
def add_no_cache_headers(resp):
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp

@cbt_server.route("/", methods=["GET", "POST"])
def index():
    global messages, background, emotion_change, cognitive_distortion_summary
    global automatic_thought, alternative_thought, plan_recommendation, improvement_goal

    if request.method == "GET":
        # 초기화
        messages = initial_messages()
        background = emotion_change = cognitive_distortion_summary = ""
        automatic_thought = alternative_thought = plan_recommendation = improvement_goal = ""

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
        global user_name, user_age, user_gender

        if not user_name and not user_age and not user_gender:
            try:
                result = llm_call_json(USER_PROMPT, user_input)
                user_name = result.get("name", "")
                user_age = int(result.get("age", 0))
                user_gender = result.get("gender", "Others")

                print(f"[INFO] 개인정보 저장: {user_name}, {user_age}, {user_gender}")
                messages.append({"role": "user", "content": user_input})

            except Exception as e:
                print(f"[WARN] 개인정보 추출 실패: {e}")
        else:
            # 일반 대화는 기존 로직
            messages.append({"role": "user", "content": user_input})

    if is_command:
        # 사용자 발화만 모아 분석
        context_text = user_only_context(messages)

        # 1) 추출 계열
        background = llm_call(EVENT_PROMPT, context_text)
        emotion_change = llm_call(EMOTION_PROMPT, context_text)
        automatic_thought = llm_call(AUTO_PROMPT, context_text)

        # 2) 인지왜곡 집계 (필요 시 화면 표시 문자열 구성)
        distortion_map = analyze_distortions_from_autos(
            automatic_thought, ALLOWED_DISTORTIONS, DISTORTION_JSON_PROMPT
        )
        cognitive_distortion_summary = format_distortion_sentence(distortion_map)

        # 3) 생성 계열
        alternative_thought = llm_call(ALTERNATIVE_PROMPT, context_text)
        improvement_goal = llm_call(GOAL_PROMPT, context_text)

        # ===== 5단계 저장 데이터 =====
        global emotion_name, emotion_score, division
        emotion_name, emotion_score, division = [], [], []
        try:
            emotion_json = llm_call_json(EMOTION_JSON_PROMPT, context_text)
            print("[DEBUG] Raw emotion_json:", emotion_json)
            for item in emotion_json:
                emotion_name.append(item.get("emotion_name", ""))
                emotion_score.append(int(item.get("emotion_score", 0)))
                division.append(item.get("division", "전"))
        except Exception as e:
            print(f"[WARN] 감정 JSON 추출 실패: {e}")

        # ===== 6단계 저장 데이터 =====
        global distortion_name, count, automatic_analysis, alternative_analysis
        distortion_name, count = [], []
        automatic_analysis, alternative_analysis = "", ""

        # 1) distortion_map → 이름/횟수 리스트 분리
        if distortion_map:
            distortion_name = list(distortion_map.keys())
            count = list(distortion_map.values())

        # 2) automatic_analysis: 자동적 사고 + 왜곡 패턴 연결
        auto_list = [s.strip() for s in automatic_thought.split(",") if s.strip()]
        analysis_lines = []
        for auto in auto_list:
            matched = max(distortion_map, key=distortion_map.get) if distortion_map else "패턴 없음"
            analysis_lines.append(f'"{auto}" → {matched} 패턴 확인')
        automatic_analysis = "\n".join(analysis_lines)

        # 3) alternative_analysis: 자동적 사고 → 대안적 사고 + 효과 설명
        alt_list = [s.strip() for s in alternative_thought.split(",") if s.strip()]
        alt_lines = []
        for auto, alt in zip(auto_list, alt_list):
            alt_lines.append(f'"{auto}" → "{alt}"')
        alternative_analysis = "\n".join(alt_lines)
        if alt_lines:
            alternative_analysis += "\n→ 이런 사고 전환은 부정적인 사고를 완화하고, 현실적인 시각을 회복하는 데 도움이 됩니다. 긍정적인 생각을 가져보세요!"

        # 4) 실천 계획 — 상담 중 말한 그대로 우선 사용, 없으면 PLAN_PROMPT 폴백
        plan_from_chat = extract_plan_from_history(messages)
        if plan_from_chat:
            plan_recommendation = plan_from_chat
        else:
            tmp = llm_call(PLAN_PROMPT, context_text)
            if tmp and tmp != "없음":
                items = [s.strip() for s in tmp.split(",") if s.strip()]
                plan_recommendation = "\n".join(f"{i+1}. {s}" for i, s in enumerate(items[:4]))
            else:
                plan_recommendation = "없음"

        plan_recommendation = strip_plan_tags(plan_recommendation)

        plan_text_list = []
        if plan_recommendation and plan_recommendation != "없음":
            lines = [p.strip() for p in plan_recommendation.split("\n") if p.strip()]
            plan_text_list = [line.split(".", 1)[1].strip() if "." in line else line for line in lines]

        # 저장 or 미저장 안내
        if user_input == "종료":
            try:
                # 1️⃣ 유저 저장 후 user_id 확보
                user_id = save_users(
                    user_name=user_name or "",
                    user_age=user_age or 0,
                    user_gender=user_gender or "Others"
                )

                # 2️⃣ 세션 저장 후 session_id 확보
                if user_id:
                    session_id = save_sessions(user_id)

                    # 3️⃣ 요약 리포트 저장 (세션에 연결)
                    if session_id:
                        save_summary_report(
                            session_id=session_id,  # ⭐ FK 연결
                            background=background or "",
                            emotion_change=emotion_change or "",
                            automatic_thought=automatic_thought or "",
                            alternative_thought=alternative_thought or "",
                            cognitive_distortion_summary=cognitive_distortion_summary or "",
                            plan_recommendation=plan_recommendation or "",
                            improvement_goal=improvement_goal or ""
                        )
                        
                        for plan in plan_text_list:
                            plan = plan.rstrip(".")
                            save_plans(
                            session_id=session_id,
                            plan_text=plan or "",
                            is_completed=False
                        )
                            
                        for name, score, div in zip(emotion_name, emotion_score, division):
                            save_emotions(
                                session_id=session_id,
                                emotion_name=name,
                                emotion_score=score,
                                division=div
                            )
                            
                        for name, cnt in zip(distortion_name, count):
                            save_distortions(
                                session_id=session_id,
                                distortion_name=name or "",
                                count=cnt or 0
                            )
                            
                        save_thoughts(
                            session_id=session_id,
                            automatic_thought=automatic_thought or "",
                            automatic_analysis=automatic_analysis or "",
                            alternative_thought=alternative_thought or "",
                            alternative_analysis=alternative_analysis or ""
                        )
                            
            except Exception as e:
                print(f"[WARN] DB 저장 프로세스 failed: {e}")

            # 저장 데이터 확인용 출력문
            print()
            print(user_name, user_gender, user_age, "\n")
            print(background, emotion_change, automatic_thought, alternative_thought, cognitive_distortion_summary, plan_recommendation, improvement_goal, "\n")
            print(plan_text_list, "\n")
            print(distortion_name, count, "\n", automatic_analysis, "\n", alternative_analysis, "\n")
            print(emotion_name, emotion_score, division, "\n")
            
            user_name, user_age, user_gender = "", 0, ""

        end_msg = (
            "✅ 상담 종료. 금일 상담 내역이 성공적으로 저장되었어요! 아래에서 요약과 분석 내용을 확인해주세요. 앱에서는 더 자세한 내용을 조회할 수 있어요😊 "
            if user_input == "종료"
            else "✔️ 상담 중단. 이번 상담 내역은 따로 저장되지 않아요! 아래에서 현재까지 진행한 요약과 분석 내용을 확인해주세요😊"
        )
        messages.append({"role": "assistant", "content": end_msg})

    else:
        chat_response = client.chat.completions.create(
            model=MODEL, temperature=0.4, messages=messages
        ).choices[0].message.content
        messages.append({"role": "assistant", "content": chat_response})

    # ✅ 화면용 히스토리: 항상 태그 숨김
    history = [(m["role"], strip_plan_tags(m["content"])) for m in messages if m["role"] in ("user", "assistant")]

    return make_response(render_template(
        "index.html",
        event=background or None,
        emotion=emotion_change or None,
        distortion=cognitive_distortion_summary or None,
        auto=automatic_thought or None,
        alternative=alternative_thought or None,
        plan=plan_recommendation or None,
        goal=improvement_goal or None,
        history=history,
        reset_on_refresh=True,
    ))
