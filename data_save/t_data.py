import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

load_dotenv()

def normalize_gender(gender_text: str):
    if gender_text.upper().startswith("M") or gender_text.startswith("남"):
        return "M"
    elif gender_text.upper().startswith("F") or gender_text.startswith("여"):
        return "F"
    else:
        return "Others"


# cbt_users 저장 
def save_users(user_name, user_age, user_gender):
    try:
        conn = mysql.connector.connect(
            host="cbt-dev-one.c0f6cyka4oe1.us-east-1.rds.amazonaws.com",
            user="admin",
            password=os.getenv("DB_PASSWORD"),
            database="cbt_system"
        )
        if conn.is_connected():
            cursor = conn.cursor()

            user_name = user_name.strip()
            user_age = int(user_age)
            user_gender = normalize_gender(user_gender)

            sql_check = """SELECT user_id FROM cbt_users 
                           WHERE user_name=%s AND user_age=%s AND user_gender=%s"""
            cursor.execute(sql_check, (user_name, user_age, user_gender))
            row = cursor.fetchone()

            if row:
                user_id = row[0]
                print(f"ℹ️ 기존 사용자 재사용 (user_id={user_id})")
            else:
                sql_insert = """INSERT INTO cbt_users (user_name, user_age, user_gender) 
                                VALUES (%s, %s, %s)"""
                cursor.execute(sql_insert, (user_name, user_age, user_gender))
                conn.commit()
                user_id = cursor.lastrowid
                print(f"✅ 새 사용자 저장 성공 (user_id={user_id})")

            return user_id

    except Error as err:
        print("❌ cbt_users 저장 실패:", err)
        return None

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


            
# cbt_sessions 저장
def save_sessions(user_id):
    try:
        conn = mysql.connector.connect(
            host="cbt-dev-one.c0f6cyka4oe1.us-east-1.rds.amazonaws.com",
            user="admin",
            password=os.getenv("DB_PASSWORD"),
            database="cbt_system"
        )
        if conn.is_connected():
            cursor = conn.cursor()
            sql = "INSERT INTO cbt_sessions (user_id) VALUES (%s)"
            cursor.execute(sql, (user_id,))  # ✅ 한 원소 튜플
            conn.commit()

            session_id = cursor.lastrowid
            print(f"✅ cbt_sessions 저장 성공 (session_id={session_id})")
            return session_id

    except Error as err:
        print("❌ cbt_sessions 저장 실패:", err)
        return None

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

            
            
# cbt_summary_report 저장
def save_summary_report(session_id, background, emotion_change, automatic_thought, alternative_thought, 
                        cognitive_distortion_summary, plan_recommendation, improvement_goal):
    try:
        conn = mysql.connector.connect(
            host="cbt-dev-one.c0f6cyka4oe1.us-east-1.rds.amazonaws.com",
            user="admin",
            password=os.getenv("DB_PASSWORD"),
            database="cbt_system"
        )
        if conn.is_connected():
            cursor = conn.cursor()
            sql = """INSERT INTO cbt_summary_report (session_id, `background`, emotion_change, automatic_thought, alternative_thought, cognitive_distortion_summary, plan_recommendation, improvement_goal) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
            values = (session_id, background, emotion_change, automatic_thought, alternative_thought, 
                        cognitive_distortion_summary, plan_recommendation, improvement_goal)
            cursor.execute(sql, values)
            conn.commit()
            print("✅ cbt_summary_report 저장 성공")

    except Error as err:
        print("❌ cbt_summary_report 저장 실패:", err)

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
         
         
            
# cbt_plans 저장
def save_plans(session_id, plan_text, is_completed):
    try:
        conn = mysql.connector.connect(
            host="cbt-dev-one.c0f6cyka4oe1.us-east-1.rds.amazonaws.com",
            user="admin",
            password=os.getenv("DB_PASSWORD"),
            database="cbt_system"
        )
        if conn.is_connected():
            cursor = conn.cursor()
            sql = "INSERT INTO cbt_plans (session_id, plan_text, is_completed) VALUES (%s, %s, %s)"
            values = (session_id, plan_text, is_completed)
            cursor.execute(sql, values)  
            conn.commit()
            print(f"✅ cbt_plans 저장 성공 ")

    except Error as err:
        print("❌ cbt_plans 저장 실패:", err)
        return None

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


# cbt_emotions 저장
def save_emotions(session_id, emotion_name, emotion_score, division):
    try:
        conn = mysql.connector.connect(
            host="cbt-dev-one.c0f6cyka4oe1.us-east-1.rds.amazonaws.com",
            user="admin",
            password=os.getenv("DB_PASSWORD"),
            database="cbt_system"
        )
        if conn.is_connected():
            cursor = conn.cursor()
            sql = "INSERT INTO cbt_emotions (session_id, emotion_name, emotion_score, division) VALUES (%s, %s, %s, %s)"
            values = (session_id, emotion_name, emotion_score, division)
            cursor.execute(sql, values)  
            conn.commit()
            print(f"✅ cbt_emotions 저장 성공 ")

    except Error as err:
        print("❌ cbt_emotions 저장 실패:", err)
        return None

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
            
            
# cbt_thoughts 저장
def save_thoughts(session_id, automatic_thought, automatic_analysis, alternative_thought, alternative_analysis):
    try:
        conn = mysql.connector.connect(
            host="cbt-dev-one.c0f6cyka4oe1.us-east-1.rds.amazonaws.com",
            user="admin",
            password=os.getenv("DB_PASSWORD"),
            database="cbt_system"
        )
        if conn.is_connected():
            cursor = conn.cursor()
            sql = "INSERT INTO cbt_thoughts (session_id,  automatic_thought, automatic_analysis, alternative_thought, alternative_analysis) VALUES (%s, %s, %s, %s, %s)"
            values = (session_id,  automatic_thought, automatic_analysis, alternative_thought, alternative_analysis)
            cursor.execute(sql, values)  
            conn.commit()
            print(f"✅ cbt_thoughts 저장 성공 ")

    except Error as err:
        print("❌ cbt_thoughts 저장 실패:", err)
        return None

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
            

# cbt_distortions 저장
def save_distortions(session_id, distortion_name, count):
    try:
        conn = mysql.connector.connect(
            host="cbt-dev-one.c0f6cyka4oe1.us-east-1.rds.amazonaws.com",
            user="admin",
            password=os.getenv("DB_PASSWORD"),
            database="cbt_system"
        )
        if conn.is_connected():
            cursor = conn.cursor()
            sql = "INSERT INTO cbt_distortions (session_id, distortion_name, count) VALUES (%s, %s, %s)"
            values = (session_id, distortion_name, count)
            cursor.execute(sql, values)  
            conn.commit()
            print(f"✅ cbt_distortions 저장 성공 ")

    except Error as err:
        print("❌ cbt_distortions 저장 실패:", err)
        return None

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()