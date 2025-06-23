# cbtchatbot/cbt_dev/dev_test.py

import mysql.connector
from mysql.connector import errorcode
from dotenv import load_dotenv
import os

load_dotenv()

DB_NAME = "report_test"

# DB 연결 (일단 DB 없이 MySQL 서버에만 연결)
conn = mysql.connector.connect(
    host="cbt-dev-one.c0f6cyka4oe1.us-east-1.rds.amazonaws.com",
    user="admin",
    password=os.getenv("DB_PASSWORD")
)
cursor = conn.cursor()

# ✅ 1단계: 데이터베이스 생성
try:
    cursor.execute(f"CREATE DATABASE {DB_NAME} DEFAULT CHARACTER SET 'utf8'")
    print(f"✅ 데이터베이스 '{DB_NAME}' 생성 완료")
except mysql.connector.Error as err:
    if err.errno == errorcode.ER_DB_CREATE_EXISTS:
        print(f"⚠️ 데이터베이스 '{DB_NAME}' 이미 존재함")
    else:
        print("❌ DB 생성 실패:", err)

# ✅ 2단계: 해당 DB 선택
try:
    conn.database = DB_NAME
except mysql.connector.Error as err:
    print("❌ DB 선택 실패:", err)
    exit(1)

# ✅ 3단계: report_table 생성
cursor.execute("""
CREATE TABLE IF NOT EXISTS reports (
    report_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
print("✅ report_table 생성 완료")

# ✅ 4단계: report_item_table 생성
cursor.execute("""
CREATE TABLE IF NOT EXISTS reports_items(
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    report_id INT,
    title VARCHAR(100),
    content TEXT,
    FOREIGN KEY (report_id) REFERENCES reports(report_id) ON DELETE CASCADE
)
""")
print("✅ report_item_table 생성 완료")

cursor.close()
conn.close()
