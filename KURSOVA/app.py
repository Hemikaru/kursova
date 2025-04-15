from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # заміни на щось надійне в реальному проєкті

DATABASE = os.path.join(os.path.dirname(__file__), 'forum.db')

# 🔌 Підключення до бази даних SQLite
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# 🏠 Головна сторінка
@app.route('/')
def index():
    conn = get_db_connection()
    threads = conn.execute('''
        SELECT threads.*, users.username 
        FROM threads 
        JOIN users ON threads.user_id = users.id
        ORDER BY threads.id DESC
    ''').fetchall()
    conn.close()
    return render_template('index.html', threads=threads)

# 🔐 Сторінка входу
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ? AND password = ?',
            (username, password)
        ).fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Невірний логін або пароль')
    return render_template('login.html')

# 📝 Сторінка реєстрації
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        conn.close()

        return redirect(url_for('login'))
    return render_template('register.html')

# 🧵 Створення теми
@app.route('/create_thread', methods=['GET', 'POST'])
def create_thread():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        conn = get_db_connection()
        conn.execute('INSERT INTO threads (title, content, user_id) VALUES (?, ?, ?)',
                     (title, content, session['user_id']))
        conn.commit()
        conn.close()

        return redirect(url_for('index'))

    return render_template('create_thread.html')

# 💬 Сторінка перегляду теми
@app.route('/thread/<int:thread_id>', methods=['GET', 'POST'])
def thread(thread_id):
    conn = get_db_connection()
    thread = conn.execute('''
        SELECT threads.*, users.username 
        FROM threads 
        JOIN users ON threads.user_id = users.id
        WHERE threads.id = ?
    ''', (thread_id,)).fetchone()

    comments = conn.execute('''
        SELECT comments.*, users.username 
        FROM comments 
        JOIN users ON comments.user_id = users.id
        WHERE comments.thread_id = ?
        ORDER BY comments.id ASC
    ''', (thread_id,)).fetchall()
    conn.close()

    return render_template('thread.html', thread=thread, comments=comments)

# ➕ Додати коментар
@app.route('/thread/<int:thread_id>/comment', methods=['POST'])
def add_comment(thread_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    content = request.form['content']

    conn = get_db_connection()
    conn.execute('INSERT INTO comments (thread_id, user_id, content) VALUES (?, ?, ?)',
                 (thread_id, session['user_id'], content))
    conn.commit()
    conn.close()

    return redirect(url_for('thread', thread_id=thread_id))

# 🚪 Вихід
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
