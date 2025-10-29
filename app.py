from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime, timedelta

app = Flask(__name__)
# IMPORTANT: A secret key is required to manage sessions (cookies) securely
app.secret_key = 'your_super_secret_key_here' 

# --- System Databases (In-Memory) ---
USERS_DB = {
    "alice": "12369874",  # A pattern sequence hash: 1-2-3-6-9-8-7-4
    "bob": "159753"      # Another pattern sequence hash
}
# Tracks active sessions: {username: login_datetime_object}
ACTIVE_SESSIONS = {}
# Stores all historical session records
SESSION_LOGS = []

# --- Core Concept: Login Route ---
@app.route('/', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        # The 'pattern' comes from the hidden input filled by JavaScript
        submitted_pattern = request.form['pattern']

        # 1. Authentication
        if username in USERS_DB and USERS_DB[username] == submitted_pattern:
            # 2. Record Login Time (Timestamp)
            login_time = datetime.now()
            ACTIVE_SESSIONS[username] = login_time
            
            # Use Flask's session object to track the logged-in user
            session['username'] = username
            session['login_time'] = login_time.strftime('%Y-%m-%d %H:%M:%S')

            print(f"LOGIN: {username} at {login_time}")
            return redirect(url_for('dashboard'))
        else:
            error = "Invalid username or pattern."
            return render_template('login.html', error=error)
            
    return render_template('login.html')

# --- User Dashboard Route ---
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    username = session['username']
    login_time_str = session['login_time']
    
    # Calculate the elapsed time since login
    login_time = datetime.strptime(login_time_str, '%Y-%m-%d %H:%M:%S')
    elapsed = datetime.now() - login_time
    
    return render_template('dashboard.html', username=username, elapsed=str(elapsed).split('.')[0])

# --- Core Concept: Logout Route ---
@app.route('/logout')
def logout():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session.pop('username', None)
    login_time_str = session.pop('login_time', None)

    if username and login_time_str:
        # Get recorded login time
        login_time = ACTIVE_SESSIONS.pop(username, None)
        # Record logout time
        logout_time = datetime.now()

        if login_time:
            # Calculate Session Duration
            session_duration = logout_time - login_time

            # Store the log
            SESSION_LOGS.append({
                "user": username,
                "login": login_time,
                "logout": logout_time,
                "duration": session_duration
            })
            print(f"LOGOUT: {username}. Duration: {session_duration}")

    return redirect(url_for('login'))

# --- Log Display Route (For admin/testing purposes) ---
@app.route('/logs')
def show_logs():
    return render_template('logs.html', logs=SESSION_LOGS)


if __name__ == '__main__':
    # Flask runs on http://127.0.0.1:5000/
    app.run(debug=True)