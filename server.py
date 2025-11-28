from flask import Flask, request, jsonify, send_from_directory
import os, zipfile, subprocess, threading, time

app = Flask(__name__, static_folder='.')
process = None
bot_dir = "mybot"

def find_main():
    files = ["main.py","bot.py","nm.py","index.py","start.py"]
    for f in files:
        if os.path.exists(f"{bot_dir}/{f}"):
            return f
    return None

@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

@app.route('/upload', methods=['POST'])
def upload():
    global process
    try:
        if 'zip' not in request.files:
            return jsonify({"success":False,"error":"No file"}), 400
        
        file = request.files['zip']
        if not file.filename.endswith('.zip'):
            return jsonify({"success":False,"error":"Only .zip files allowed"}), 400

        # Clean old
        if os.path.exists(bot_dir):
            os.system("rm -rf mybot")
        os.makedirs(bot_dir, exist_ok=True)

        path = "temp.zip"
        file.save(path)

        # Check if valid ZIP
        if not zipfile.is_zipfile(path):
            os.remove(path)
            return jsonify({"success":False,"error":"Invalid or corrupted ZIP file"}), 400

        # Extract with password check
        try:
            with zipfile.ZipFile(path, 'r') as z:
                z.extractall(bot_dir)
        except RuntimeError as e:
            if "encrypted" in str(e):
                os.remove(path)
                return jsonify({"success":False,"error":"Password protected ZIP not allowed"}), 400
            else:
                os.remove(path)
                return jsonify({"success":False,"error":"ZIP extraction failed"}), 400

        os.remove(path)

        # Install requirements
        if os.path.exists(f"{bot_dir}/requirements.txt"):
            os.system(f"pip install -r {bot_dir}/requirements.txt --quiet")

        # Kill old bot
        if process:
            process.kill()
            time.sleep(1)

        # Run bot
        main_file = find_main()
        if main_file:
            process = subprocess.Popen(["python", main_file], cwd=bot_dir)
            return jsonify({"success":True, "file":main_file})
        else:
            return jsonify({"success":False,"error":"No main.py/bot.py/nm.py found"}), 400

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
        main_file = find_main()
        if main_file:
            process = subprocess.Popen(["python", main_file], cwd=bot_dir)
    return "restarted"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
