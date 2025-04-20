from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'supersecretkey'

DATABASE = os.path.join(os.path.dirname(__file__), 'forum.db')
AVATAR_FOLDER = os.path.join('static', 'avatars')
os.makedirs(AVATAR_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = AVATAR_FOLDER

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

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
        SELECT comments.*, users.username, users.xp 
        FROM comments 
        JOIN users ON comments.user_id = users.id
        WHERE comments.thread_id = ?
        ORDER BY comments.id ASC
    ''', (thread_id,)).fetchall()
    conn.close()

    return render_template('thread.html', thread=thread, comments=comments)

@app.route('/thread/<int:thread_id>/comment', methods=['POST'])
def add_comment(thread_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    content = request.form['content']
    parent_id = request.form.get('parent_id')

    conn = get_db_connection()
    conn.execute('INSERT INTO comments (thread_id, user_id, content) VALUES (?, ?, ?)',
                 (thread_id, session['user_id'], content))
    comment_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]

    conn.execute('UPDATE users SET xp = xp + 10 WHERE id = ?', (session['user_id'],))

    if parent_id:
        parent = conn.execute('SELECT * FROM comments WHERE id = ?', (parent_id,)).fetchone()
        if parent and parent['user_id'] != session['user_id']:
            conn.execute('''
                INSERT INTO notifications (recipient_id, sender_id, thread_id, comment_id)
                VALUES (?, ?, ?, ?)
            ''', (parent['user_id'], session['user_id'], thread_id, comment_id))

    conn.commit()
    conn.close()

    return redirect(url_for('thread', thread_id=thread_id))

@app.route('/edit_comment/<int:comment_id>', methods=['POST'])
def edit_comment(comment_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    new_content = request.form['content']

    conn = get_db_connection()
    comment = conn.execute('SELECT * FROM comments WHERE id = ?', (comment_id,)).fetchone()

    if comment and comment['user_id'] == session['user_id']:
        conn.execute('UPDATE comments SET content = ? WHERE id = ?', (new_content, comment_id))
        conn.commit()
    conn.close()

    return redirect(url_for('thread', thread_id=comment['thread_id']))

@app.route('/notifications')
def notifications():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    notes = conn.execute('''
        SELECT notifications.*, users.username AS sender_name 
        FROM notifications 
        JOIN users ON notifications.sender_id = users.id
        WHERE recipient_id = ?
        ORDER BY notifications.id DESC
    ''', (session['user_id'],)).fetchall()
    conn.close()

    return jsonify([
        {
            "id": note['id'],
            "message": f"{note['sender_name']} відповів на ваш коментар",
            "thread_id": note['thread_id'],
            "comment_id": note['comment_id']
        }
        for note in notes
    ])

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    comments = conn.execute('''
        SELECT comments.content, comments.created_at, threads.title, threads.id as thread_id
        FROM comments
        JOIN threads ON comments.thread_id = threads.id
        WHERE comments.user_id = ?
        ORDER BY comments.created_at DESC
    ''', (session['user_id'],)).fetchall()
    conn.close()

    level = user['xp'] // 100
    xp_progress = user['xp'] % 100
    xp_percent = int((xp_progress / 100) * 100)
    next_level_xp = 100

    return render_template('profile.html', user=user, comments=comments, level=level, xp=user['xp'], xp_progress=xp_progress, xp_percent=xp_percent, next_level_xp=next_level_xp)

@app.route('/user/<int:user_id>')
def user_profile(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        conn.close()
        return "Користувача не знайдено", 404

    comments = conn.execute('''
        SELECT comments.content, comments.created_at, threads.title, threads.id as thread_id
        FROM comments
        JOIN threads ON comments.thread_id = threads.id
        WHERE comments.user_id = ?
        ORDER BY comments.created_at DESC
    ''', (user_id,)).fetchall()
    conn.close()

    level = user['xp'] // 100
    xp_progress = user['xp'] % 100
    xp_percent = int((xp_progress / 100) * 100)
    next_level_xp = 100

    return render_template('user_profile.html', user=user, comments=comments, level=level, xp=user['xp'], xp_progress=xp_progress, xp_percent=xp_percent, next_level_xp=next_level_xp)

@app.route('/profile/update', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    new_username = request.form['username']
    file = request.files.get('avatar')

    avatar_path = None
    if file and file.filename:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        avatar_path = '/' + file_path.replace('\\', '/').replace(os.path.sep, '/')

    conn = get_db_connection()
    if avatar_path:
        conn.execute('UPDATE users SET username = ?, avatar = ? WHERE id = ?', (new_username, avatar_path, session['user_id']))
    else:
        conn.execute('UPDATE users SET username = ? WHERE id = ?', (new_username, session['user_id']))
    conn.commit()
    conn.close()

    session['username'] = new_username
    return redirect(url_for('profile'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)