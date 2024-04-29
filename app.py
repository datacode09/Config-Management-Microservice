from flask import Flask, jsonify, request, abort
from flask_httpauth import HTTPBasicAuth
import sqlite3
import os

app = Flask(__name__)
auth = HTTPBasicAuth()

# Define the database path
DATABASE = 'configurations.db'

# User data could alternatively be stored securely in a database or other secure storage mechanism
users = {
    "admin": "secret"
}

@auth.get_password
def get_pw(username):
    if username in users:
        return users[username]
    return None

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """ Create database and table if they don't exist """
    if not os.path.exists(DATABASE):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE configurations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                data TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

@app.route('/config/<name>', methods=['GET'])
@auth.login_required
def get_config(name):
    conn = get_db_connection()
    config = conn.execute('SELECT * FROM configurations WHERE name = ?', (name,)).fetchone()
    conn.close()
    if config:
        return jsonify({"status": "success", "data": config['data']}), 200
    else:
        return jsonify({"status": "error", "message": "Configuration not found"}), 404

@app.route('/config', methods=['POST'])
@auth.login_required
def create_config():
    if not request.json or 'name' not in request.json or 'data' not in request.json:
        abort(400, description="Missing name or data in request payload.")
    name = request.json['name']
    data = request.json['data']
    conn = get_db_connection()
    conn.execute('INSERT INTO configurations (name, data) VALUES (?, ?)', (name, data))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Configuration created"}), 201

@app.route('/config/<name>', methods=['PUT'])
@auth.login_required
def update_config(name):
    if not request.json or 'data' not in request.json:
        abort(400, description="Missing data in request payload.")
    data = request.json['data']
    conn = get_db_connection()
    conn.execute('UPDATE configurations SET data = ? WHERE name = ?', (data, name))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Configuration updated"}), 200

@app.route('/config/<name>', methods=['DELETE'])
@auth.login_required
def delete_config(name):
    conn = get_db_connection()
    conn.execute('DELETE FROM configurations WHERE name = ?', (name,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Configuration deleted"}), 200

if __name__ == '__main__':
    init_db()  # Initialize the database
    app.run(debug=True, host='0.0.0.0', ssl_context='adhoc')
