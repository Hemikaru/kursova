from flask import Flask, render_template, request, redirect, session, url_for
import pymysql

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Замінити на власний у реальному проєкті

# 🔌 Функція підключення до бази даних
def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',        # ← свій користувач
        password='',        # ← якщо є пароль, впиши тут
        database='forum',   # ← назва твоєї бази
        cursorclass=pymysql.cursors.DictCursor
    )

# 🏠 Головна сторінка
@app.route('/')
def index():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM threads ORDER BY created_at DESC")
        threads = cursor.fetchall()
    conn.close()
    return render_template('index.html', threads=threads)

# 🔐 Сторінка входу
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
            user = cursor.fetchone()
        conn.close()

        if user:
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
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
            conn.commit()
        conn.close()

        return redirect(url_for('login'))
    return render_template('register.html')

# 🧵 Створення теми
@app.route('/create_thread', methods=['GET', 'POST'])
def create_thread():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO threads (title, content, author) VALUES (%s, %s, %s)",
                           (title, content, session['username']))
            conn.commit()
        conn.close()

        return redirect(url_for('index'))

    return render_template('create_thread.html')

# 💬 Сторінка перегляду теми
@app.route('/thread/<int:thread_id>', methods=['GET', 'POST'])
def thread(thread_id):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM threads WHERE id = %s", (thread_id,))
        thread = cursor.fetchone()

        cursor.execute("SELECT * FROM comments WHERE thread_id = %s ORDER BY created_at", (thread_id,))
        comments = cursor.fetchall()
    conn.close()

    return render_template('thread.html', thread=thread, comments=comments)

# ➕ Додати коментар
@app.route('/thread/<int:thread_id>/comment', methods=['POST'])
def add_comment(thread_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    content = request.form['content']

    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("INSERT INTO comments (thread_id, author, content) VALUES (%s, %s, %s)",
                       (thread_id, session['username'], content))
        conn.commit()
    conn.close()

    return redirect(url_for('thread', thread_id=thread_id))

# 🚪 Вихід
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
