from flask import Flask, request, jsonify, send_from_directory
import os
import zipfile
import subprocess
import threading
import time

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB limit

bot_process = None
bot_dir = "user_bot"

def find_startup():
    files = ["main.py", "bot.py", "nm.py", "index.py", "start.py"]
    for f in files:
        if os.path.exists(os.path.join(bot_dir, f)):
            return f
    return None

def run_bot():
    global bot_process
    startup = find_startup()
    if not startup: return False
    cmd = ["python", startup]
    bot_process = subprocess.Popen(cmd, cwd=bot_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    def stream():
        for line in iter(bot_process.stdout.readline, b''):
            if line: print("BOT →", line.decode().strip())
    threading.Thread(target=stream, daemon=True).start()
    return True

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/upload', methods=['POST'])
def upload():
    global bot_process
    try:
        if 'botzip' not in request.files:
            return jsonify({"success": False, "error": "No file"}), 400
        file = request.files['botzip']
        if not file.filename.endswith('.zip'):
            return jsonify({"success": False, "error": "ZIP only"}), 400

        if os.path.exists(bot_dir):
            os.system("rm -rf " + bot_dir)
        os.makedirs(bot_dir, exist_ok=True)

        zip_path = "temp.zip"
        file.save(zip_path)
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(bot_dir)
        os.remove(zip_path)

        req = os.path.join(bot_dir, "requirements.txt")
        if os.path.exists(req):
            os.system(f"pip install -r {req}")

        if bot_process:
            bot_process.kill()

        startup = find_startup()
        if startup and run_bot():
            return jsonify({"success": True, "startup": startup})
        else:
            return jsonify({"success": False, "error": "No main.py/bot.py found"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/stop')
def stop():
    global bot_process
    if bot_process:
        bot_process.kill()
    return "stopped"

@app.route('/restart')
def restart():
    global bot_process
    if bot_process:
        bot_process.kill()
        time.sleep(2)
        run_bot()
    return "restarted"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
