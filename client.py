import requests
import threading
import time
import os
import socket
from flask import Flask, request, jsonify

app = Flask(__name__)

timer_remaining = 0
shutdown_flag = False
client_ip = socket.gethostbyname(socket.gethostname())

@app.route('/set_timer', methods=['POST'])
def set_timer():
    global timer_remaining
    data = request.json
    timer_remaining = data.get("timer", 0)
    
    print(f"Timer received: {timer_remaining} seconds")
    threading.Thread(target=start_timer, args=(timer_remaining,)).start()
    
    return {"status": "Timer Set"}, 200

@app.route('/status', methods=['GET'])
def status():
    return jsonify({"ip": client_ip, "timer_remaining": timer_remaining})

def start_timer(timer):
    global timer_remaining
    while timer_remaining > 0:
        time.sleep(1)
        timer_remaining -= 1
    
    if not shutdown_flag:
        print("Locking system...")
        lock_system()

def lock_system():
    if os.name == "nt":  # Windows
        os.system("rundll32.exe user32.dll,LockWorkStation")
    elif os.name == "posix":  # Linux/Mac
        os.system("gnome-screensaver-command -l")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
