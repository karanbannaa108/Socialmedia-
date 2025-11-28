from flask import Flask, request, jsonify, send_from_directory
import os, zipfile, subprocess, threading, time, signal

app = Flask(__name__, static_folder='.')

process = None
bot_folder = "mybot"

def find_main():
    files = ["main.py","bot.py","nm.py","index.py","start.py"]
    for f in files:
        if os.path.exists(f"mybot/{f}"):
            return f
    return None

def run():
    global process
    file = find_main()
    if not file: return False
    process = subprocess.Popen(
        ["python", file], cwd="mybot",
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    def logs():
        for line in process.stdout:
            print("BOT →", line.decode().strip())
    threading.Thread(target=logs, daemon=True).start()
    return True

@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

@app.route('/upload', methods=['POST'])
def upload():
    global process
    try:
        if 'zip' not in request.files:
            return jsonify({"success":False,"error":"No file"}), 400
        zipf = request.files['zip']
        if not zipf.filename.endswith('.zip'):
            return jsonify({"success":False,"error":"ZIP only"}), 400

        if os.path.exists(bot_folder):
            os.system("rm -rf mybot")
        os.makedirs(bot_folder, exist_ok=True)

        path = "temp.zip"
        zipf.save(path)
        with zipfile.ZipFile(path, 'r') as z:
            z.extractall(bot_folder)
        os.remove(path)

        req = "mybot/requirements.txt"
        if os.path.exists(req):
            os.system(f"pip install -r {req} --quiet")

        if process:
            process.kill()
        time.sleep(1)

        main_file = find_main()
        if main_file and run():
            return jsonify({"success":True, "file":main_file})
        else:
            return jsonify({"success":False,"error":"No main.py/bot.py found"}), 400
    except Exception as e:
        return jsonify({"success":False,"error":str(e)}), 500

@app.route('/stop')
def stop():
    global process
    if process:
        process.kill()
    return "stopped"

@app.route('/restart')
def restart():
    global process
    if process:
        process.kill()
        time.sleep(2)
        run()
    return "restarted"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
