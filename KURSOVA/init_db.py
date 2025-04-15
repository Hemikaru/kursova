import sqlite3
import os

DATABASE = os.path.join(os.path.dirname(__file__), 'forum.db')

if os.path.exists(DATABASE):
    os.remove(DATABASE)

conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

# 🔧 Створення таблиць під SQLite
cursor.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    );
''')

cursor.execute('''
    CREATE TABLE threads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        user_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
''')

cursor.execute('''
    CREATE TABLE comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT NOT NULL,
        thread_id INTEGER,
        user_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(thread_id) REFERENCES threads(id),
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
''')

conn.commit()
conn.close()

print("✅ SQLite база створена з таблицями users, threads, comments!")
