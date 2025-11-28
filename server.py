from flask import Flask, request, jsonify, send_from_directory
import os
import zipfile
import subprocess
import threading
import time
import json

app = Flask(__name__, static_folder='.')

bot_process = None
bot_dir = "user_bot"

def find_startup():
    files = ["main.py", "bot.py", "nm.py", "index.py", "start.py"]
    for f in files:
        path = os.path.join(bot_dir, f)
        if os.path.exists(path):
            return f
    return None

def run_bot():
    global bot_process
    startup = find_startup()
    if not startup:
        return False
    cmd = ["python", startup]
    bot_process = subprocess.Popen(
        cmd, cwd=bot_dir,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        bufsize=1, universal_newlines=True
    )
    
    def stream_output():
        for line in iter(bot_process.stdout.readline, ''):
            if line:
                print(f"BOT LOG: {line.strip()}")
    threading.Thread(target=stream_output, daemon=True).start()
    return True

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/upload', methods=['POST'])
def upload():
    global bot_process
    try:
        if 'botzip' not in request.files:
            return jsonify({"success": False, "error": "No file uploaded"}), 400

        file = request.files['botzip']
        if not file.filename.endswith('.zip'):
            return jsonify({"success": False, "error": "Only ZIP files allowed"}), 400

        # Clean old bot
        if os.path.exists(bot_dir):
            os.system(f"rm -rf {bot_dir}")
        os.makedirs(bot_dir, exist_ok=True)

        # Save and extract ZIP
        zip_path = "temp_bot.zip"
        file.save(zip_path)
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(bot_dir)
        os.remove(zip_path)

        # Install requirements if exists
        req_path = os.path.join(bot_dir, "requirements.txt")
        if os.path.exists(req_path):
            os.system(f"pip install -r {req_path} --quiet")

        # Stop old bot if running
        if bot_process:
            bot_process.kill()
            time.sleep(1)

        # Run new bot
        startup = find_startup()
        if startup and run_bot():
            return jsonify({"success": True, "startup": startup})
        else:
            return jsonify({"success": False, "error": "No startup file (main.py/bot.py/nm.py) found"}), 400

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/stop')
def stop():
    global bot_process
    try:
        if bot_process:
            bot_process.kill()
            time.sleep(1)
        return "stopped"
    except Exception as e:
        return str(e), 500

@app.route('/restart')
def restart():
    global bot_process
    try:
        if bot_process:
            bot_process.kill()
            time.sleep(2)
        run_bot()
        return "restarted"
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
