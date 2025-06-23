from flask import Blueprint, request, jsonify
import mysql.connector
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

report = Blueprint("report",__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@report.route("/save_report", methods=["POST"])
def save_report():
    try:
        posture_conn = mysql.connector.connect(
            host="cbt-dev-one.c0f6cyka4oe1.us-east-1.rds.amazonaws.com",
            user="admin",
            password=os.getenv("DB_PASSWORD"),
            database="posture_test1"
        )
        cursor = posture_conn.cursor()

        # ✅ 최신 pitch 값 조회
        cursor.execute("SELECT pitch_angle FROM pitch ORDER BY created_at DESC LIMIT 1")
        pitch_result = cursor.fetchone()
        pitch = pitch_result[0] if pitch_result else '알 수 없음'

        # ✅ 최신 distance 값 조회
        cursor.execute("SELECT distance_cm FROM distance ORDER BY created_at DESC LIMIT 1")
        distance_result = cursor.fetchone()
        distance = distance_result[0] if distance_result else '알 수 없음'

        print("📥 최신 pitch:", pitch)
        print("📥 최신 distance:", distance)

        # GPT에게 보낼 프롬프트 구성
        prompt = f"""
너는 자세 분석 리포트를 생성하는 헬스 코치야.
아래 데이터를 참고해서 제목 + 설명 형식의 리포트 항목 5개를 만들어줘.

✅ 형식 (반드시 아래처럼 만들어야 해):
- [제목만]
  설명 문장 (1~2문장)

예시:
- [모니터 거리 조정 필요]
  사용자와 모니터의 거리가 35cm로 너무 가깝습니다. 거리를 넓히는 것이 좋습니다.

- [거북목 증상 주의]
  고개 숙임 각도가 높아 목과 어깨에 부담을 줄 수 있습니다. 틈틈이 스트레칭을 해주세요.

📌 규칙:
- 숫자 리스트(1., 2. 등)는 절대 쓰지 마.
- 각 항목 앞에는 반드시 `- [제목]` 형식을 써줘.
- 제목은 “제목: 설명” 형식이 아니라, **제목만** 써.
- 총 5개 항목을 만들어야 해.

데이터:
- 고개 숙임 각도(코, 어깨 랜드마크 선을 통해 측정, 목각도라고 하면될듯),(Pitch): {pitch}도
- 사용자와 모니터 사이의 거리(distance): {distance}cm
"""

        # GPT 호출
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        result_text = response.choices[0].message.content

        # DB 연결
        conn = mysql.connector.connect(
            host="cbt-dev-one.c0f6cyka4oe1.us-east-1.rds.amazonaws.com",
            user="admin",
            password=os.getenv("DB_PASSWORD"),
            database="report_test"
        )
        cursor = conn.cursor()

        # reports 테이블에 리포트 세션 저장
        cursor.execute("INSERT INTO reports (user_id) VALUES (%s)", ("test_user",))
        report_id = cursor.lastrowid

        # report_items 테이블에 항목 5개 저장
        for line in result_text.strip().split("\n- "):
            if not line.strip():
                continue
            try:
                title_line, content_line = line.split("\n", 1)
                title = title_line.replace("-", "").strip()
                content = content_line.strip()
                cursor.execute(
                    "INSERT INTO reports_items (report_id, title, content) VALUES (%s, %s, %s)",
                    (report_id, title, content)
                )
            except ValueError:
                continue  # 항목 형식이 이상하면 건너뜀

        conn.commit()
        return jsonify({"status": "success", "report_id": report_id})

    except Exception as e:
        print("❌ 서버 처리 중 에러:", e)
        return jsonify({"status": "error", "message": str(e)}), 500

    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass



# # ✅ 리포트 조회 API
# @report.route("/get_report/<int:report_id>", methods=["GET"])
# def get_report(report_id):
#     conn = mysql.connector.connect(
#         host="cbt-dev-one.c0f6cyka4oe1.us-east-1.rds.amazonaws.com",
#         user="admin",
#         password="20020219",
#         database="report_test"
#     )
#     cursor = conn.cursor()

#     cursor.execute("SELECT title, content FROM report_items WHERE report_id = %s", (report_id,))
#     rows = cursor.fetchall()
#     cursor.close()
#     conn.close()

#     items = [{"title": title, "content": content} for title, content in rows]
#     return jsonify(items)



@report.route("/get_latest_report/", methods=["GET"])
def get_latest_report():
    try:
        conn = mysql.connector.connect(
            host="cbt-dev-one.c0f6cyka4oe1.us-east-1.rds.amazonaws.com",
            user="admin",
            password=os.getenv("DB_PASSWORD"),
            database="report_test"
        )
        cursor = conn.cursor()

        cursor.execute("SELECT report_id FROM reports ORDER BY created_at DESC LIMIT 1")
        result = cursor.fetchone()

        if not result:
            cursor.close()
            conn.close()
            return jsonify([])

        report_id = result[0]

        cursor.execute("SELECT title, content FROM reports_items WHERE report_id = %s", (report_id,))
        items = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify([
            {"title": title, "content": content}
            for title, content in items
        ])

    except Exception as e:
        print("❌ get_latest_report 에러:", e)
        return jsonify({"status": "error", "message": str(e)}), 500

    
    