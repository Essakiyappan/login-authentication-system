from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# ✅ Secure secret key (use environment variable in production)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your_super_secret_key_here')

# --- In-Memory Databases ---
USERS_DB = {
    "alice": "12369874",  # pattern: 1-2-3-6-9-8-7-4
    "bob": "159753"       # pattern: 1-5-9-7-5-3 (example)
}

ACTIVE_SESSIONS = {}  # {username: login_time}
SESSION_LOGS = []      # list of dicts: user, login, logout, duration

# --- Optional Session Timeout (auto-logout after inactivity) ---
@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=15)

# --- Login Route ---
@app.route('/', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        submitted_pattern = request.form.get('pattern')

        if not username or not submitted_pattern:
            return render_template('login.html', error="Please enter both username and pattern.")

        # Authenticate
        if username in USERS_DB and USERS_DB[username] == submitted_pattern:
            session.clear()  # prevent session fixation
            login_time = datetime.now()
            ACTIVE_SESSIONS[username] = login_time
            session['username'] = username
            session['login_time'] = login_time.strftime('%Y-%m-%d %H:%M:%S')

            print(f"[LOGIN] {username} at {login_time}")
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid username or pattern.")

    return render_template('login.html')


# --- Dashboard Route ---
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    login_time_str = session['login_time']

    try:
        login_time = datetime.strptime(login_time_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return redirect(url_for('logout'))

    elapsed = datetime.now() - login_time

    return render_template('dashboard.html', username=username, elapsed=str(elapsed).split('.')[0])


# --- Logout Route ---
@app.route('/logout')
def logout():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session.pop('username', None)
    login_time_str = session.pop('login_time', None)

    if username and login_time_str:
        login_time = ACTIVE_SESSIONS.pop(username, None)
        logout_time = datetime.now()

        if login_time:
            duration = logout_time - login_time
            SESSION_LOGS.append({
                "user": username,
                "login": login_time,
                "logout": logout_time,
                "duration": duration
            })
            print(f"[LOGOUT] {username} | Duration: {duration}")

    return redirect(url_for('login'))


# --- Logs Route (Admin view) ---
@app.route('/logs')
def show_logs():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('logs.html', logs=SESSION_LOGS)


if __name__ == '__main__':
    app.run(debug=True)
