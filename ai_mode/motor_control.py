from flask import Blueprint, request, jsonify
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

motor_control = Blueprint("motor_control", __name__)

db_config = {
    'host': 'cbt-dev-one.c0f6cyka4oe1.us-east-1.rds.amazonaws.com',
    'user': 'admin',
    'password': os.getenv("DB_PASSWORD"),
    'database': 'posture_test1'
}

@motor_control.route("/save_pitch",methods=["POST"])
def save_pitch():
    try:
        data = request.json
        # print("📤 수신된 목각도 JSON 데이터:", data)

        # ✅ 값 유무 및 형식 확인
        pitch_raw = data.get("pitch")
        if pitch_raw is None:
            return jsonify({"success": False, "message": "Missing pitch_angle"}), 400

        try:
            pitch = float(pitch_raw)
        except (TypeError, ValueError):
            return jsonify({"success": False, "message": "Invalid pitch format"}), 400

        # ✅ DB 연결 및 저장
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO pitch (pitch_angle) VALUES (%s)", (pitch,))
        conn.commit()

        cursor.close()
        conn.close()
        # (type: {type(pitch)})
        print(f"📥 받은 pitch: {pitch}")
        return jsonify({"success": True, "message": "pitch saved"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@motor_control.route("/save_distance", methods=["POST"])
def save_distance():
    try:
        data = request.json
        # print("📤 수신된 거리 JSON 데이터:", data)

        # ✅ 값 유무 및 형식 확인
        distance_raw = data.get("distance_cm")
        if distance_raw is None:
            return jsonify({"success": False, "message": "Missing distance_cm"}), 400

        try:
            distance = float(distance_raw)
        except (TypeError, ValueError):
            return jsonify({"success": False, "message": "Invalid distance format"}), 400

        # ✅ DB 연결 및 저장
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO distance (distance_cm) VALUES (%s)", (distance,))
        conn.commit()

        cursor.close()
        conn.close()
        # (type: {type(distance)})
        print(f"📥 받은 distance: {distance}")
        return jsonify({"success": True, "message": "Distance saved"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@motor_control.route("/save_distance", methods=["GET"])
def save_distance_get():
    print(f"❌ 잘못된 GET 요청 감지 - IP: {request.remote_addr}")
    return jsonify({"error": "GET method not allowed"}), 405
    
    
    
    
    
    
@motor_control.route("/get_pitch",methods=["GET"])
def get_pitch():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute("SELECT pitch_angle FROM pitch ORDER BY created_at DESC LIMIT 1")
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if result:
            pitch_angle = result[0]  # distance_cm 값만 반환됨
            return jsonify({"success": True, "pitch_angle": pitch_angle})
        else:
            return jsonify({"success": False, "message": "No data found"}), 404

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    
@motor_control.route("/get_distance",methods=["GET"])
def get_distance():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute("SELECT distance_cm FROM distance ORDER BY created_at DESC LIMIT 1")
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if result:
            distance_cm = result[0]  # distance_cm 값만 반환됨
            return jsonify({"success": True, "distance_cm": distance_cm})
        else:
            return jsonify({"success": False, "message": "No data found"}), 404

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500