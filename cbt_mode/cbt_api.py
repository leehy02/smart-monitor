# routes/cbt_api.py
from flask import Blueprint, jsonify
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()
cbt_api = Blueprint("cbt_api", __name__)

@cbt_api.route("/summary_report", methods=["GET"], strict_slashes=False)
def get_latest_summary_report():
    """
    전체 세션 중 가장 최신 세션의 요약 리포트 1건 반환
    """
    conn = None
    cursor = None
    try:
        # 1) DB 연결
        conn = mysql.connector.connect(
            host="cbt-dev-one.c0f6cyka4oe1.us-east-1.rds.amazonaws.com",
            user="admin",
            password=os.getenv("DB_PASSWORD"),
            database="cbt_system"
        )
        cursor = conn.cursor(dictionary=True)

        # 2) 최신 세션의 요약 1건 조회 (한 번의 쿼리로 해결)
        cursor.execute("""
            SELECT
                s.session_id,
                s.session_datetime,
                sr.background,
                sr.emotion_change,
                sr.automatic_thought,
                sr.cognitive_distortion_summary,
                sr.alternative_thought,
                sr.improvement_goal,
                sr.plan_recommendation
            FROM cbt_sessions AS s
            JOIN cbt_summary_report AS sr
              ON sr.session_id = s.session_id
            ORDER BY s.session_datetime DESC
            LIMIT 1
        """)

        row = cursor.fetchone()

        if not row:
            return jsonify({"status": "not_found", "message": "요약 리포트가 없습니다."}), 404

        return jsonify(row)

    except Exception as e:
        print("❌ /summary_report 에러:", e)
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        try:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()
        except:
            pass
   
        
@cbt_api.route("/emotion_report", methods = ["GET"], strict_slashes=False)
def get_latest_emotion_report():
    conn = None #나중에 사용할거라 미리 선언하기
    cursor = None
    try:
        conn = mysql.connector.connect(
            host="cbt-dev-one.c0f6cyka4oe1.us-east-1.rds.amazonaws.com",
            user="admin",
            password=os.getenv("DB_PASSWORD"),
            database="cbt_system"
        )
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                s.session_id,
                s.session_datetime,
                e.emotion_name,
                e.emotion_score,
                e.division
            FROM cbt_sessions AS s
            JOIN cbt_emotions AS e
            ON e.session_id = s.session_id
            WHERE s.session_id = (
                SELECT s2.session_id
                FROM cbt_sessions AS s2
                ORDER BY s2.session_datetime DESC
                LIMIT 1
            )
            ORDER BY FIELD(e.division, '전', '후'), e.emotion_score DESC, e.emotion_name
        """)


        row = cursor.fetchall()

        if not row:
            return jsonify({"status": "not_found", "message": "요약 리포트가 없습니다."}), 404

        return jsonify(row)

    except Exception as e:
        print("❌ /emotion_report 에러:", e)
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        try:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()
        except:
            pass
        
        
@cbt_api.route("/user_info", methods=["GET"], strict_slashes=False)
def get_user_info():
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(
            host="cbt-dev-one.c0f6cyka4oe1.us-east-1.rds.amazonaws.com",
            user="admin",
            password=os.getenv("DB_PASSWORD"),
            database="cbt_system"
        )
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                user_id,
                user_name,
                user_age,
                user_gender,
                created_at
            FROM cbt_users
            ORDER BY created_at DESC
            LIMIT 1
        """)

        row = cursor.fetchone()

        if not row:
            return jsonify({"status": "not_found", "message": "사용자 정보가 없습니다."}), 404
        if "created_at" in row:
            del row["created_at"]

        print(row)
        
        return jsonify(row)

    except Exception as e:
        print("❌ /user_info 에러:", e)
        return jsonify({"status": "error", "message": str(e)}), 500

    finally:
        try:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()
        except:
            pass

