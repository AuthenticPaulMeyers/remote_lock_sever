import tkinter as tk
from tkinter import messagebox
import requests
import threading

# List of client computers (Replace with actual LAN IPs)
clients = ["http://192.168.1.101:5001", "http://192.168.1.102:5001"]

def send_timer():
    try:
        timer = int(timer_entry.get())
        for client in clients:
            url = f"{client}/set_timer"
            response = requests.post(url, json={"timer": timer})
            print(f"Sent to {client}: {response.status_code}")

        messagebox.showinfo("Success", f"Timer set for all clients: {timer} seconds")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def update_dashboard():
    client_statuses = []
    
    for client in clients:
        try:
            response = requests.get(f"{client}/status", timeout=3)
            if response.status_code == 200:
                data = response.json()
                client_statuses.append(f"{data['ip']} - {data['timer_remaining']} sec")
        except:
            client_statuses.append(f"{client} - Offline")
    
    # Update Dashboard
    status_label.config(text="\n".join(client_statuses))
    
    # Refresh every 5 seconds
    root.after(5000, update_dashboard)

# GUI Setup
root = tk.Tk()
root.title("Admin Panel")

tk.Label(root, text="Enter Timer (seconds):").pack()
timer_entry = tk.Entry(root)
timer_entry.pack()

tk.Button(root, text="Set Timer", command=send_timer).pack()

# Dashboard Section
tk.Label(root, text="\nActive Clients & Timers:").pack()
status_label = tk.Label(root, text="Fetching...", justify="left")
status_label.pack()

# Start auto-update for dashboard
update_dashboard()

root.mainloop()
