import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

load_dotenv()

def save_summary_to_db(summary_result):
    try:
        conn = mysql.connector.connect(
            host="cbt-dev-one.c0f6cyka4oe1.us-east-1.rds.amazonaws.com",
            user="admin",
            password=os.getenv("DB_PASSWORD"),
            database="cbt_chatbot_test"
        )
        if conn.is_connected():
            cursor = conn.cursor()
            sql = "INSERT INTO summary_table (summary_text) VALUES (%s)"
            cursor.execute(sql, (summary_result,))
            conn.commit()
            print("✅ summary 저장 성공")

    except Error as err:
        print("❌ DB 저장 실패:", err)

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
