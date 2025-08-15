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
        
                # ✅ pitch 최근 10개 값 가져오기
        cursor.execute("SELECT pitch_angle FROM pitch ORDER BY created_at DESC LIMIT 10")
        pitch_rows = cursor.fetchall()
        pitch_list = [row[0] for row in reversed(pitch_rows)]  # 시간순 정렬
        pitch_avg = round(sum(pitch_list) / len(pitch_list), 2) if pitch_list else '알 수 없음'
        pitch_sequence = ' → '.join([f"{round(p, 1)}" for p in pitch_list])

        # ✅ distance 최근 10개 값 가져오기
        cursor.execute("SELECT distance_cm FROM distance ORDER BY created_at DESC LIMIT 10")
        distance_rows = cursor.fetchall()
        distance_list = [row[0] for row in reversed(distance_rows)]  # 시간순 정렬
        distance_avg = round(sum(distance_list) / len(distance_list), 2) if distance_list else '알 수 없음'
        distance_sequence = ' → '.join([f"{round(d, 1)}" for d in distance_list])
        
        print("\n",pitch_list,pitch_avg)
        print(distance_list,distance_avg)
        print()

        # # ✅ 최신 pitch 값 조회
        # cursor.execute("SELECT pitch_angle FROM pitch ORDER BY created_at DESC LIMIT 1")
        # pitch_result = cursor.fetchone()
        # pitch = pitch_result[0] if pitch_result else '알 수 없음'

        # # ✅ 최신 distance 값 조회
        # cursor.execute("SELECT distance_cm FROM distance ORDER BY created_at DESC LIMIT 1")
        # distance_result = cursor.fetchone()
        # distance = distance_result[0] if distance_result else '알 수 없음'

        # print("📥 최신 pitch:", pitch)
        # print("📥 최신 distance:", distance)

        # GPT에게 보낼 프롬프트 구성
        prompt = f"""
너는 자세 분석 리포트를 생성하는 헬스 코치야.
아래 📊 최근 자세 데이터를 참고해서 제목 + 설명 형식의 리포트 항목 5개를 만들어줘.

✅ 형식 (반드시 아래처럼 만들어야 해):
- [제목만]
  설명 문장 (1~2문장)

예시:
- 거리 변화 추세 분석 - [모니터 거리 조정 필요]
  사용자와 모니터의 거리가 35cm로 너무 가깝습니다. 거리를 넓히는 것이 좋습니다.

- 목각도 평균값 기준 피드백 - [거북목 증상 주의]
  고개 숙임 각도가 높아 목과 어깨에 부담을 줄 수 있습니다. 틈틈이 스트레칭을 해주세요.

📌 규칙:
- 숫자 리스트(1., 2. 등)는 절대 쓰지 마.
- 각 항목 앞에는 반드시 `- [제목]` 형식을 써줘.
- 제목은 “제목: 설명” 형식이 아니라, **제목만** 써.
- 제목은 예시 처럼 각 항목 유형 이름 - [제목이름] 이런 식으로 쓰도록해. 유형은 아래 순서를 따라줘.
- 총 5개 항목을 만들어야 해.

📌 각 항목 유형:
규칙에서 5개의 항목을 만든다고 했잖아. 각 항목의 유형을 알려줄게
1.목각도 변화 추세 분석
예시:
- [점점 고개가 더 숙여지고 있어요]	
  최근 10초 간 목각도가 점점 낮아지고 있어 거북목 위험이 커지고 있습니다. 스트레칭을 권장해요.
  
2.거리 변화 추세 분석
예시:
- [자세 변화가 너무 급격해요]
  거리 변화가 60cm → 40cm 등 급격히 변하고 있어 주의가 필요합니다. 자세를 안정적으로 유지해보세요.
  
3.목각도 평균값 기준 피드백
예시:
- [목 스트레칭을 꼭 해주세요]
  최근 목각도 평균이 52도 이상으로 높습니다. 30분마다 스트레칭을 해주면 도움이 됩니다.
   
4.거리 평균값 기준 피드백
예시:
- [거리 평균이 너무 가까워요]
  최근 사용자-모니터 평균 거리가 35cm로, 눈의 피로를 유발할 수 있습니다. 50cm 이상 유지해보세요.
  
5.전체적인 자세 피드백
예시:
- [좋은 자세 유지 중이에요]
목각도와 거리 모두 안정적인 흐름을 보이고 있어요. 지금처럼만 유지해도 좋아요.

전체적인 예시이고 우리 프로젝트에서 목각도는 50도 이상일시 정상, 미만은 거북목이라고 판단할거야.
거리는 30~50cm는 정상, 30cm 미만은 가깝고 50cm 초과는 멀다고 판단할거야. 이 기준을 기반으로 받아오는 목각도와 거리 데이터를 분석해서 위와 같은 리포트를 생성해주면돼.

📊 최근 자세 데이터:
- 고개 숙임 각도(Pitch) 변화: {pitch_sequence}
- 평균 각도: {pitch_avg}도

- 사용자-모니터 거리(Distance) 변화: {distance_sequence}
- 평균 거리: {distance_avg}cm
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

    
    