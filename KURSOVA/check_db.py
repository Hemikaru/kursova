import sqlite3
import os

DATABASE = os.path.join(os.path.dirname(__file__), 'forum.db')

conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("📦 Таблиці в базі даних:")
for table in tables:
    print("-", table[0])

conn.close()
