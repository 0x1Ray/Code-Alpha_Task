# TaskManager - Simple Todo Web Application
# Built for CS351 Web Security Course Project
# Author: Alex Chen
# Date: March 2024

from flask import Flask, request, render_template_string, redirect, session, jsonify, make_response
import sqlite3
import os
import hashlib
import datetime

app = Flask(__name__)
app.secret_key = "my_secret_key_2024"

DATABASE = 'tasks.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    return conn

def init_database():
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            email TEXT
        )
    ''')
    
    # Tasks table  
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            title TEXT,
            description TEXT,
            completed INTEGER DEFAULT 0,
            created_date TEXT
        )
    ''')
    
    # Add test user
    cursor.execute("INSERT OR IGNORE INTO users VALUES (1, 'admin', 'password123', 'admin@tasks.com')")
    cursor.execute("INSERT OR IGNORE INTO users VALUES (2, 'testuser', 'test123', 'test@tasks.com')")
    
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return '''
    <html>
    <head><title>TaskManager</title></head>
    <body>
        <h1>Welcome to TaskManager</h1>
        <a href="/login">Login</a> | <a href="/register">Register</a>
    </body>
    </html>
    '''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return '''
        <html>
        <head><title>Login</title></head>
        <body>
            <h2>Login</h2>
            <form method="post">
                Username: <input type="text" name="username"><br><br>
                Password: <input type="password" name="password"><br><br>
                <input type="submit" value="Login">
            </form>
        </body>
        </html>
        '''
    
    username = request.form['username']
    password = request.form['password']
    
    conn = get_db()
    cursor = conn.cursor()
    
    # TODO: Fix this query later - prof mentioned something about SQL injection
    query = "SELECT * FROM users WHERE username = '" + username + "' AND password = '" + password + "'"
    cursor.execute(query)
    user = cursor.fetchone()
    conn.close()
    
    if user:
        session['user_id'] = user[0] 
        session['username'] = user[1]
        return redirect('/dashboard')
    else:
        return "Invalid login credentials"

@app.route('/register', methods=['GET', 'POST'])  
def register():
    if request.method == 'GET':
        return '''
        <html>
        <head><title>Register</title></head>
        <body>
            <h2>Register New Account</h2>
            <form method="post">
                Username: <input type="text" name="username" required><br><br>
                Password: <input type="password" name="password" required><br><br>
                Email: <input type="email" name="email" required><br><br>
                <input type="submit" value="Register">
            </form>
        </body>
        </html>
        '''
    
    username = request.form['username']
    password = request.form['password']  
    email = request.form['email']
    
    # Simple password hash
    password_hash = hashlib.md5(password.encode()).hexdigest()
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        query = f"INSERT INTO users (username, password, email) VALUES ('{username}', '{password_hash}', '{email}')"
        cursor.execute(query)
        conn.commit()
        conn.close()
        return "Registration successful! <a href='/login'>Login here</a>"
    except:
        conn.close()
        return "Username already exists"

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    
    user_id = session['user_id']
    username = session['username']
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE user_id = ?", (user_id,))
    tasks = cursor.fetchall()
    conn.close()
    
    task_list = ""
    for task in tasks:
        status = "✓" if task[5] else "○"
        task_list += f"<li>{status} {task[2]} - {task[3]} <a href='/delete_task/{task[0]}'>Delete</a></li>"
    
    return f'''
    <html>
    <head><title>Dashboard</title></head>
    <body>
        <h2>Welcome {username}!</h2>
        <h3>Your Tasks:</h3>
        <ul>{task_list}</ul>
        
        <h3>Add New Task:</h3>
        <form method="post" action="/add_task">
            Title: <input type="text" name="title" required><br><br>
            Description: <input type="text" name="description"><br><br>
            <input type="submit" value="Add Task">
        </form>
        
        <p><a href="/search">Search Tasks</a> | <a href="/export">Export Data</a> | <a href="/logout">Logout</a></p>
    </body>
    </html>
    '''

@app.route('/add_task', methods=['POST'])
def add_task():
    if 'user_id' not in session:
        return redirect('/login')
    
    user_id = session['user_id']
    title = request.form['title']
    description = request.form['description']
    created_date = str(datetime.datetime.now())
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (user_id, title, description, created_date) VALUES (?, ?, ?, ?)",
                   (user_id, title, description, created_date))
    conn.commit()
    conn.close()
    
    return redirect('/dashboard')

@app.route('/search')
def search():
    if 'user_id' not in session:
        return redirect('/login')
        
    search_term = request.args.get('q', '')
    
    if search_term:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE user_id = ? AND title LIKE ?", 
                      (session['user_id'], f'%{search_term}%'))
        results = cursor.fetchall()
        conn.close()
        
        result_html = ""
        for task in results:
            result_html += f"<li>{task[2]} - {task[3]}</li>"
    else:
        result_html = ""
    
    return f'''
    <html>
    <head><title>Search Tasks</title></head>
    <body>
        <h2>Search Your Tasks</h2>
        <form method="get">
            <input type="text" name="q" value="{search_term}" placeholder="Search tasks...">
            <input type="submit" value="Search">
        </form>
        
        <h3>Results for: {search_term}</h3>
        <ul>{result_html}</ul>
        
        <a href="/dashboard">Back to Dashboard</a>
    </body>
    </html>
    '''

@app.route('/delete_task/<int:task_id>')
def delete_task(task_id):
    # Quick delete function - should probably add some checks later
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    
    return redirect('/dashboard')

@app.route('/export')
def export_data():
    if 'user_id' not in session:
        return redirect('/login')
    
    user_id = session['user_id']
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE user_id = ?", (user_id,))
    tasks = cursor.fetchall()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    # Simple data export
    export_data = {
        'user': {
            'id': user[0],
            'username': user[1], 
            'email': user[3]
        },
        'tasks': []
    }
    
    for task in tasks:
        export_data['tasks'].append({
            'id': task[0],
            'title': task[2],
            'description': task[3],
            'completed': task[5],
            'date': task[6]
        })
    
    response = make_response(jsonify(export_data))
    response.headers['Content-Disposition'] = 'attachment; filename=tasks_export.json'
    return response

@app.route('/user/<int:user_id>')
def view_user(user_id):
    # Public user profile view
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT username, email FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return f'''
        <html>
        <body>
            <h2>User Profile</h2>
            <p>Username: {user[0]}</p>
            <p>Email: {user[1]}</p>
        </body>
        </html>
        '''
    else:
        return "User not found"

@app.route('/admin/users')
def admin_users():
    # Admin panel - need to add auth check sometime
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email FROM users")
    users = cursor.fetchall()
    conn.close()
    
    user_list = ""
    for user in users:
        user_list += f"<li>ID: {user[0]}, Username: {user[1]}, Email: {user[2]} <a href='/admin/delete/{user[0]}'>Delete</a></li>"
    
    return f'''
    <html>
    <body>
        <h2>Admin - All Users</h2>
        <ul>{user_list}</ul>
    </body>
    </html>
    '''

@app.route('/admin/delete/<int:user_id>')
def admin_delete_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    cursor.execute("DELETE FROM tasks WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    return redirect('/admin/users')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    init_database()
    app.run(debug=True, host='0.0.0.0', port=5000)