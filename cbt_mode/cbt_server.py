from flask import Blueprint, request, render_template
from data_save.t_data import save_summary_to_db
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

cbt_server = Blueprint("cbt_server", __name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

messages = [{
    "role": "system",
    "content": """
        당신은 직장인의 스트레스, 불안, 우울 완화를 돕는 인지행동치료(CBT) 전문 챗봇입니다.

        사용자가 모니터를 켰을 때 자동으로 실행되며, 짧은 대화를 통해 사용자의 감정 상태를 점검하고 인지 왜곡을 인식하도록 도와주며, 대안적 사고를 유도합니다.

        ### 역할
        - 심리치료사가 아닌 ‘심리 코치’의 어조를 사용해 주세요.
        - 진단이나 강한 주장 없이, 질문과 공감으로 유도해 주세요.
        - 사용자의 입력을 바탕으로 필요한 CBT 단계(감정 탐색 → 자동적 사고 → 인지 왜곡 → 대안적 사고 → 마무리)를 선택해 대응하세요.

        ### 기본 대화 흐름
        1. 현재 감정 상태나 최근 상황을 부드럽게 묻기
        2. 자동적 사고를 인식하도록 질문
        3. 인지 왜곡 패턴(흑백논리, 과잉 일반화 등)을 설명하며 해당 여부 탐색
        4. 현실적이고 부드러운 대안적 사고 유도
        5. 긍정 문장 또는 호흡 유도 등으로 대화 마무리

        이 챗봇은 하루의 시작을 긍정적으로 유도하는 것이 목표입니다. 사용자의 감정을 판단하지 말고, 공감하며 안내해 주세요.
        """
}]

summary_result = ""
emotion_result = ""
distortion_result = ""

@cbt_server.route("/", methods=["GET", "POST"])
def index():
    global summary_result, emotion_result, distortion_result
    response = ""

    if request.method == "POST":
        user_input = request.form["user_input"]
        messages.append({"role": "user", "content": user_input})

        if user_input.strip() == "종료":
            summary_result = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "CBT 요약"}] + messages[1:]
            ).choices[0].message.content

            save_summary_to_db(summary_result)

            emotion_result = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "감정 점수 분석"}] + messages[1:]
            ).choices[0].message.content

            distortion_result = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "인지 왜곡 분석"}] + messages[1:]
            ).choices[0].message.content

            response = "상담 종료. 아래 요약과 분석 내용을 확인해보세요 😊"

        else:
            chat_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages
            ).choices[0].message.content
            messages.append({"role": "assistant", "content": chat_response})
            response = chat_response

    return render_template("index.html", 
        response=response,
        summary=summary_result,
        emotion=emotion_result,
        distortion=distortion_result
    )
