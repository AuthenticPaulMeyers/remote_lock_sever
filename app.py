# Admin Panel (Server) - Flask API & PyQt GUI
# Client Agent (Listener) - Background Service on Client Machines

import socket
import os
import threading
import sqlite3
import time
import requests
from flask import Flask, request, jsonify
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QListWidget, QSpinBox

# Database Setup
def setup_database():
    conn = sqlite3.connect('clients.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS clients (
                        id INTEGER PRIMARY KEY,
                        ip TEXT UNIQUE,
                        mac TEXT,
                        status TEXT,
                        lock_timer INTEGER)''')
    conn.commit()
    conn.close()
setup_database()

# Flask API for Client Management
app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register_client():
    data = request.json
    ip = data.get('ip')
    mac = data.get('mac')
    
    conn = sqlite3.connect('clients.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO clients (ip, mac, status, lock_timer) VALUES (?, ?, 'online', 0)", (ip, mac))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Client registered'}), 200

@app.route('/lock', methods=['POST'])
def lock_client():
    data = request.json
    ip = data.get('ip')
    os.system(f"ping -c 1 {ip}")  # Check if the client is reachable
    os.system(f"ssh {ip} 'rundll32.exe user32.dll,LockWorkStation'")  # Lock Windows client
    return jsonify({'message': f'Lock command sent to {ip}'})

@app.route('/set_timer', methods=['POST'])
def set_timer():
    data = request.json
    ip = data.get('ip')
    timer = data.get('timer')
    
    conn = sqlite3.connect('clients.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE clients SET lock_timer = ? WHERE ip = ?", (timer, ip))
    conn.commit()
    conn.close()
    return jsonify({'message': f'Timer set for {ip} to {timer} minutes'})

@app.route('/get_clients', methods=['GET'])
def get_clients():
    conn = sqlite3.connect('clients.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clients")
    clients = cursor.fetchall()
    conn.close()
    return jsonify({'clients': clients})

# Admin Panel GUI
class AdminPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Admin Panel')
        self.setGeometry(100, 100, 400, 400)
        layout = QVBoxLayout()

        self.client_list = QListWidget()
        layout.addWidget(QLabel('Connected Clients'))
        layout.addWidget(self.client_list)

        self.lock_button = QPushButton('Lock Selected Client')
        self.lock_button.clicked.connect(self.lock_selected_client)
        layout.addWidget(self.lock_button)
        
        self.timer_input = QSpinBox()
        self.timer_input.setRange(1, 120)
        layout.addWidget(QLabel('Set Timer (minutes)'))
        layout.addWidget(self.timer_input)
        
        self.set_timer_button = QPushButton('Set Timer for Selected Client')
        self.set_timer_button.clicked.connect(self.set_timer_for_client)
        layout.addWidget(self.set_timer_button)
        
        self.refresh_button = QPushButton('Refresh List')
        self.refresh_button.clicked.connect(self.load_clients)
        layout.addWidget(self.refresh_button)
        
        self.setLayout(layout)
        self.load_clients()
    
    def load_clients(self):
        self.client_list.clear()
        response = requests.get('http://127.0.0.1:5000/get_clients').json()
        for client in response['clients']:
            self.client_list.addItem(f"{client[1]} - {client[2]} ({client[3]}, Timer: {client[4]} min)")
    
    def lock_selected_client(self):
        selected_item = self.client_list.currentItem()
        if selected_item:
            ip = selected_item.text().split(' - ')[0]
            requests.post('http://127.0.0.1:5000/lock', json={'ip': ip})
            self.load_clients()
    
    def set_timer_for_client(self):
        selected_item = self.client_list.currentItem()
        if selected_item:
            ip = selected_item.text().split(' - ')[0]
            timer = self.timer_input.value()
            requests.post('http://127.0.0.1:5000/set_timer', json={'ip': ip, 'timer': timer})
            self.load_clients()

# Start Flask in Background
def run_flask():
    app.run(port=5000, debug=False, use_reloader=False)

t = threading.Thread(target=run_flask)
t.start()

# Run GUI
if __name__ == '__main__':
    app = QApplication([])
    window = AdminPanel()
    window.show()
    app.exec()

# Client Agent (Python script for clients)
import requests
import time
import socket
import threading

def get_mac_address():
    import uuid
    return ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0,2*6,2)][::-1])

server_url = 'http://127.0.0.1:5000/register'
client_ip = socket.gethostbyname(socket.gethostname())
client_mac = get_mac_address()

def check_timer():
    while True:
        response = requests.get('http://127.0.0.1:5000/get_clients').json()
        for client in response['clients']:
            if client[1] == client_ip and client[4] > 0:
                time.sleep(client[4] * 60)
                os.system("rundll32.exe user32.dll,LockWorkStation")
                break
        time.sleep(10)

threading.Thread(target=check_timer, daemon=True).start()

while True:
    try:
        requests.post(server_url, json={'ip': client_ip, 'mac': client_mac})
    except Exception as e:
        print("Error connecting to server:", e)
    time.sleep(10)  # Send heartbeat every 10 sec
