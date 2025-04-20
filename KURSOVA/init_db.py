import sqlite3
import os

DATABASE = os.path.join(os.path.dirname(__file__), 'forum.db')

if os.path.exists(DATABASE):
    os.remove(DATABASE)

conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

# 🔧 Користувачі
cursor.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        avatar TEXT DEFAULT 'default.png',
        xp INTEGER DEFAULT 0
    );
''')

# 🧵 Теми
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

# 💬 Коментарі
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

# 🔔 Сповіщення
cursor.execute('''
    CREATE TABLE notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipient_id INTEGER NOT NULL,
        sender_id INTEGER NOT NULL,
        thread_id INTEGER NOT NULL,
        comment_id INTEGER NOT NULL,
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(recipient_id) REFERENCES users(id),
        FOREIGN KEY(sender_id) REFERENCES users(id),
        FOREIGN KEY(thread_id) REFERENCES threads(id),
        FOREIGN KEY(comment_id) REFERENCES comments(id)
    );
''')

# 👍 Лайки / Дизлайки для тем
cursor.execute('''
    CREATE TABLE thread_votes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        thread_id INTEGER NOT NULL,
        value INTEGER NOT NULL CHECK(value IN (1, -1)),
        UNIQUE(user_id, thread_id),
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(thread_id) REFERENCES threads(id)
    );
''')

# 👍 Лайки / Дизлайки для коментарів
cursor.execute('''
    CREATE TABLE comment_votes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        comment_id INTEGER NOT NULL,
        value INTEGER NOT NULL CHECK(value IN (1, -1)),
        UNIQUE(user_id, comment_id),
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(comment_id) REFERENCES comments(id)
    );
''')

conn.commit()
conn.close()

print("✅ SQLite база створена з таблицями users, threads, comments, notifications, thread_votes, comment_votes!")
