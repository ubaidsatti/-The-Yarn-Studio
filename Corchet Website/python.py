"""
Flask one-file website: app.py

What this contains:
- A simple multi-page website (home, about, contact) served by Flask
- A small contact form that saves messages into a local SQLite database
- Inline CSS and simple responsive layout

Run instructions:
1. Create a virtual environment (recommended):
   python -m venv venv
   source venv/bin/activate   # on Windows: venv\Scripts\activate
2. Install Flask:
   pip install Flask
3. Run the app:
   python app.py
4. Open http://127.0.0.1:5000 in your browser

You can change SECRET_KEY and DEBUG as needed.

This single file is intentionally self-contained so you can copy-paste it into app.py and run.
"""

from flask import Flask, request, g, redirect, url_for, render_template_string
import sqlite3
import os
from datetime import datetime

# ---------- Configuration ----------
DATABASE = os.path.join(os.path.dirname(__file__), 'site.db')
SECRET_KEY = os.environ.get('FLASK_SECRET', 'dev-secret-key')
DEBUG = True

# ---------- App setup ----------
app = Flask(__name__)
app.config.from_mapping(
    SECRET_KEY=SECRET_KEY,
    DATABASE=DATABASE,
    DEBUG=DEBUG,
)

# ---------- Database helpers ----------
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
        db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.executescript('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT,
        message TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    ''')
    db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Initialize DB on startup
with app.app_context():
    init_db()

# ---------- Templates (render_template_string) ----------
BASE_TEMPLATE = '''
<!doctype html>



{% endblock %}
'''

# ---------- Routes ----------
@app.route('/')
def home():
    db = get_db()
    cur = db.execute('SELECT name, message, created_at FROM messages ORDER BY id DESC LIMIT 5')
    messages = cur.fetchall()
    return render_template_string(HOME_TEMPLATE, base=BASE_TEMPLATE, title='Home', messages=messages, year=datetime.utcnow().year)

@app.route('/about')
def about():
    return render_template_string(ABOUT_TEMPLATE, base=BASE_TEMPLATE, title='About', year=datetime.utcnow().year)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    success = False
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        email = request.form.get('email','').strip()
        message = request.form.get('message','').strip()
        if not name or not message:
            # keep page showing validation errors (browser will usually enforce required fields)
            pass
        else:
            db = get_db()
            db.execute('INSERT INTO messages (name, email, message, created_at) VALUES (?, ?, ?, ?)',
                       (name, email, message, datetime.utcnow().isoformat()))
            db.commit()
            success = True
            # after successful POST we redirect to avoid resubmission on refresh
            return redirect(url_for('contact') + '?sent=1')
    if request.args.get('sent') == '1':
        success = True
    return render_template_string(CONTACT_TEMPLATE, base=BASE_TEMPLATE, title='Contact', success=success, request=request, year=datetime.utcnow().year)

# Simple API endpoint that returns number of messages (example of a small JSON API)
@app.route('/api/stats')
def api_stats():
    db = get_db()
    cur = db.execute('SELECT COUNT(*) as cnt FROM messages')
    count = cur.fetchone()['cnt']
    return { 'messages': count }

# ---------- Run server ----------
if __name__ == '__main__':
    # Create database file if it doesn't exist
    if not os.path.exists(app.config['DATABASE']):
        with app.app_context():
            init_db()
        print('Initialized new database at', app.config['DATABASE'])
    app.run(host='127.0.0.1', port=5000, debug=app.config['DEBUG'])