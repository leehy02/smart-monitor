# routes/cbt_api.py
from flask import Blueprint, jsonify, request
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


@cbt_api.route("/distortions_report", methods=["GET"], strict_slashes=False)
def get_latest_distortions_report():
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
                s.session_id,
                s.session_datetime,
                d.distortion_id,
                d.distortion_name,
                d.count
            FROM cbt_sessions AS s
            JOIN cbt_distortions AS d
            ON d.session_id = s.session_id
            WHERE s.session_id = (
                SELECT s2.session_id
                FROM cbt_sessions AS s2
                ORDER BY s2.session_datetime DESC
                LIMIT 1
            )
            ORDER BY d.distortion_id, d.distortion_name, d.count DESC
        """)

        rows = cursor.fetchall()

        if not rows:
            return jsonify({"status": "not_found", "message": "사용자 정보가 없습니다."}), 404

        print(rows)
        
        return jsonify(rows)

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


@cbt_api.route("/thoughts_report", methods=["GET"], strict_slashes=False)
def get_latest_thoughts_report():
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
                s.session_id,
                s.session_datetime,
                t.automatic_thought,
                t.automatic_analysis,
                t.alternative_thought,
                t.alternative_analysis
            FROM cbt_sessions AS s
            JOIN cbt_thoughts AS t
              ON t.session_id = s.session_id
            ORDER BY s.session_datetime DESC
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
        
        
        

@cbt_api.route("/plans_report", methods=["GET", "POST"], strict_slashes=False)
def get_latest_plans_report():
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

        # ---------------------------
        # GET: 최신 세션의 계획 리스트 반환
        # ---------------------------
        if request.method == "GET":
            cursor.execute("""
                SELECT
                    s.session_id,
                    s.session_datetime,
                    p.plan_id,
                    p.plan_text,
                    p.is_completed
                FROM cbt_sessions AS s
                JOIN cbt_plans AS p
                  ON p.session_id = s.session_id
                WHERE s.session_id = (
                    SELECT s2.session_id
                    FROM cbt_sessions AS s2
                    ORDER BY s2.session_datetime DESC
                    LIMIT 1
                )
                ORDER BY p.plan_id
            """)
            rows = cursor.fetchall()

            if not rows:
                return jsonify({"status": "not_found", "message": "사용자 정보가 없습니다."}), 404

            # 혹시 행에 created_at 같은 불필요 컬럼이 있다면 제거
            for r in rows:
                r.pop("created_at", None)

            return jsonify(rows), 200

        # ---------------------------
        # POST: 체크박스 완료 여부 업데이트
        # ---------------------------
        data = request.get_json(force=True) or {}
        plan_id = data.get("plan_id")
        is_completed_raw = data.get("is_completed")

        if plan_id is None:
            return jsonify({"status": "error", "message": "plan_id가 필요합니다."}), 400

        # 다양한 입력을 0/1로 안전 변환
        def to_int01(v):
            if isinstance(v, bool):
                return 1 if v else 0
            try:
                # "1","0","true","false" 등 처리
                if isinstance(v, str):
                    low = v.strip().lower()
                    if low in ("true", "t", "yes", "y", "1"):
                        return 1
                    if low in ("false", "f", "no", "n", "0"):
                        return 0
                return 1 if int(v) == 1 else 0
            except Exception:
                return 0

        is_completed = to_int01(is_completed_raw)

        cursor.execute(
            "UPDATE cbt_plans SET is_completed=%s WHERE plan_id=%s",
            (is_completed, int(plan_id))
        )
        conn.commit()
        updated = cursor.rowcount  # 1이면 정상 업데이트

        return jsonify({
            "status": "ok" if updated == 1 else "noop",
            "plan_id": int(plan_id),
            "is_completed": is_completed,
            "updated": updated
        }), 200

    except Exception as e:
        print("❌ /plans_report 에러:", e)
        return jsonify({"status": "error", "message": str(e)}), 500

    finally:
        try:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()
        except:
            pass
