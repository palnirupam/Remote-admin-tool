import socket
import os
import json
import base64
import threading
import time
from datetime import datetime

HOST = "0.0.0.0"
PORT = 5000

clients = {}  # {client_id: {"conn": conn, "addr": addr, "info": {}}}
active_client_id = None

def print_banner():
    """Display banner"""
    print("\n" + "="*80)
    print("  REMOTE ADMINISTRATION TOOL - Enterprise Edition v2.0")
    print("  CLI Server with Multi-Client, Screenshot & File Transfer")
    print("="*80 + "\n")

def print_menu():
    """Display menu"""
    print("\n" + "-"*80)
    print("QUICK COMMANDS:")
    print("  [1] ipconfig          [2] whoami           [3] dir")
    print("  [4] systeminfo        [5] tasklist         [6] cd")
    print("")
    print("ADVANCED FEATURES:")
    print("  [screenshot] - Capture client screen and save")
    print("  [download]   - Download file from client")
    print("  [upload]     - Upload file to client")
    print("  [sysinfo]    - Get detailed system information")
    print("")
    print("SYSTEM CONTROL:")
    print("  [restart]    - Restart client PC")
    print("  [shutdown]   - Shutdown client PC")
    print("  [lock]       - Lock client screen")
    print("")
    print("PROCESS CONTROL:")
    print("  [find]       - Find process by name")
    print("  [kill]       - Kill process by name")
    print("")
    print("CLIENT MANAGEMENT:")
    print("  [clients]    - List all connected clients")
    print("  [switch]     - Switch to different client")
    print("  [info]       - Show current client info")
    print("")
    print("  [menu] - Show this menu  |  [exit] - Disconnect current client")
    print("-"*80 + "\n")

def list_clients():
    """Display all connected clients"""
    if not clients:
        print("⚠️  No clients connected\n")
        return
    
    print("\n" + "="*80)
    print("CONNECTED CLIENTS:")
    print("="*80)
    for i, (client_id, data) in enumerate(clients.items(), 1):
        info = data.get("info", {})
        active = "🟢 ACTIVE" if client_id == active_client_id else "⚪"
        print(f"  [{i}] {active} {info.get('hostname', 'Unknown')} - {data['addr'][0]}")
        print(f"      OS: {info.get('os', 'Unknown')} | User: {info.get('user', 'Unknown')}")
    print("="*80 + "\n")

def switch_client():
    """Switch to different client"""
    global active_client_id
    
    if not clients:
        print("⚠️  No clients connected\n")
        return
    
    list_clients()
    
    try:
        choice = int(input("Select client number: "))
        if 1 <= choice <= len(clients):
            active_client_id = list(clients.keys())[choice - 1]
            info = clients[active_client_id].get("info", {})
            print(f"\n✓ Switched to: {info.get('hostname', 'Unknown')} ({clients[active_client_id]['addr'][0]})\n")
        else:
            print("❌ Invalid choice\n")
    except:
        print("❌ Invalid input\n")

def capture_screenshot():
    """Capture and save screenshot"""
    if not active_client_id:
        print("⚠️  No active client\n")
        return
    
    try:
        conn = clients[active_client_id]["conn"]
        print("📸 Requesting screenshot...")
        
        conn.send("SCREENSHOT".encode())
        data = conn.recv(1048576)  # 1MB buffer for image
        
        response = json.loads(data.decode())
        
        if response.get("status") == "success":
            img_data = base64.b64decode(response.get("data"))
            
            filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            with open(filename, 'wb') as f:
                f.write(img_data)
            
            print(f"✓ Screenshot saved: {filename}\n")
        else:
            print(f"❌ Screenshot failed: {response.get('message')}\n")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")

def download_file():
    """Download file from client"""
    if not active_client_id:
        print("⚠️  No active client\n")
        return
    
    filepath = input("Enter file path on client (e.g., C:\\file.txt): ").strip()
    if not filepath:
        return
    
    try:
        conn = clients[active_client_id]["conn"]
        print(f"📥 Downloading {filepath}...")
        
        conn.send(f"DOWNLOAD:{filepath}".encode())
        data = conn.recv(10485760)  # 10MB buffer
        
        response = json.loads(data.decode())
        
        if response.get("status") == "success":
            file_data = base64.b64decode(response.get("data"))
            filename = response.get("filename")
            
            with open(filename, 'wb') as f:
                f.write(file_data)
            
            print(f"✓ File downloaded: {filename} ({len(file_data)} bytes)\n")
        else:
            print(f"❌ Download failed: {response.get('message')}\n")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")

def upload_file():
    """Upload file to client"""
    if not active_client_id:
        print("⚠️  No active client\n")
        return
    
    filepath = input("Enter local file path to upload: ").strip()
    if not filepath or not os.path.exists(filepath):
        print("❌ File not found\n")
        return
    
    try:
        with open(filepath, 'rb') as f:
            file_data = base64.b64encode(f.read()).decode()
        
        filename = os.path.basename(filepath)
        conn = clients[active_client_id]["conn"]
        
        print(f"📤 Uploading {filename}...")
        
        cmd = f"UPLOAD:{filename}:{file_data}"
        conn.send(cmd.encode())
        
        data = conn.recv(4096)
        response = json.loads(data.decode())
        
        if response.get("status") == "success":
            print(f"✓ {response.get('message')}\n")
        else:
            print(f"❌ Upload failed: {response.get('message')}\n")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")

def accept_clients():
    """Accept multiple clients in background"""
    server_socket = socket.socket()
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    
    print(f"✓ Server started on {HOST}:{PORT}")
    print("Waiting for client connections...\n")
    
    while True:
        try:
            conn, addr = server_socket.accept()
            
            # Receive client info
            try:
                data = conn.recv(4096).decode()
                client_info = json.loads(data)
            except:
                client_info = {"hostname": "Unknown", "os": "Unknown", "user": "Unknown"}
            
            client_id = f"{addr[0]}:{addr[1]}"
            clients[client_id] = {
                "conn": conn,
                "addr": addr,
                "info": client_info
            }
            
            print(f"✓ Client connected: {client_info.get('hostname', 'Unknown')} from {addr[0]}")
            print(f"  Total clients: {len(clients)}\n")
            
        except Exception as e:
            print(f"❌ Accept error: {str(e)}")

# Start server in background
print_banner()
threading.Thread(target=accept_clients, daemon=True).start()
time.sleep(1)

# Wait for first client
print("Waiting for first client to connect...")
while not clients:
    time.sleep(0.5)

# Auto-select first client
active_client_id = list(clients.keys())[0]
info = clients[active_client_id].get("info", {})
print(f"\n✓ Auto-selected: {info.get('hostname', 'Unknown')} ({clients[active_client_id]['addr'][0]})")

print_menu()

# Main command loop
while True:
    try:
        if not active_client_id or active_client_id not in clients:
            if clients:
                active_client_id = list(clients.keys())[0]
            else:
                print("⚠️  No clients connected. Waiting...")
                while not clients:
                    time.sleep(1)
                active_client_id = list(clients.keys())[0]
        
        cmd = input("Remote-Admin> ")
        
        if not cmd:
            continue
        
        # Handle shortcuts
        if cmd == "menu":
            print_menu()
            continue
        elif cmd == "clients":
            list_clients()
            continue
        elif cmd == "switch":
            switch_client()
            continue
        elif cmd == "screenshot":
            capture_screenshot()
            continue
        elif cmd == "download":
            download_file()
            continue
        elif cmd == "upload":
            upload_file()
            continue
        elif cmd == "1":
            cmd = "ipconfig"
        elif cmd == "2":
            cmd = "whoami"
        elif cmd == "3":
            cmd = "dir"
        elif cmd == "4":
            cmd = "systeminfo"
        elif cmd == "5":
            cmd = "tasklist"
        elif cmd == "6":
            cmd = "cd"
        elif cmd == "info":
            info = clients[active_client_id].get("info", {})
            print(f"\n{'='*80}")
            print("CURRENT CLIENT INFO:")
            print(f"{'='*80}")
            print(f"  Hostname: {info.get('hostname', 'Unknown')}")
            print(f"  OS: {info.get('os', 'Unknown')}")
            print(f"  User: {info.get('user', 'Unknown')}")
            print(f"  IP: {clients[active_client_id]['addr'][0]}")
            print(f"  Port: {clients[active_client_id]['addr'][1]}")
            print(f"{'='*80}\n")
            continue
        elif cmd == "sysinfo":
            cmd = "SYSINFO"
        elif cmd == "restart":
            confirm = input("⚠️  Restart client PC? (yes/no): ")
            if confirm.lower() != "yes":
                print("Cancelled.\n")
                continue
            cmd = "shutdown /r /t 0"
        elif cmd == "shutdown":
            confirm = input("⚠️  Shutdown client PC? (yes/no): ")
            if confirm.lower() != "yes":
                print("Cancelled.\n")
                continue
            cmd = "shutdown /s /t 0"
        elif cmd == "lock":
            cmd = "rundll32.exe user32.dll,LockWorkStation"
        elif cmd == "find":
            process = input("Process name: ")
            if process:
                cmd = f"tasklist | findstr {process}"
        elif cmd == "kill":
            process = input("Process name (e.g., notepad.exe): ")
            if process:
                confirm = input(f"⚠️  Kill {process}? (yes/no): ")
                if confirm.lower() == "yes":
                    cmd = f"taskkill /F /IM {process}"
                else:
                    print("Cancelled.\n")
                    continue
        
        # Send command
        try:
            conn = clients[active_client_id]["conn"]
            conn.send(cmd.encode())
        except Exception as e:
            print(f"❌ Failed to send command: {str(e)}")
            print("⚠️  Client may have disconnected\n")
            del clients[active_client_id]
            active_client_id = None
            continue
        
        if cmd.lower() == "exit":
            print("✓ Disconnecting client...\n")
            try:
                conn.close()
            except:
                pass
            del clients[active_client_id]
            active_client_id = None
            
            if clients:
                active_client_id = list(clients.keys())[0]
                info = clients[active_client_id].get("info", {})
                print(f"✓ Switched to: {info.get('hostname', 'Unknown')}\n")
            else:
                print("⚠️  No more clients. Waiting for new connection...\n")
                while not clients:
                    time.sleep(1)
                active_client_id = list(clients.keys())[0]
                info = clients[active_client_id].get("info", {})
                print(f"✓ New client connected: {info.get('hostname', 'Unknown')}\n")
            continue
        
        data = conn.recv(65536)
        
        if not data:
            print("⚠️  Client disconnected unexpectedly\n")
            try:
                conn.close()
            except:
                pass
            del clients[active_client_id]
            active_client_id = None
            
            if clients:
                active_client_id = list(clients.keys())[0]
            continue
        
        output = data.decode(errors="ignore")
        
        # Check for JSON response
        try:
            response = json.loads(output)
            resp_type = response.get("type", "")
            
            if resp_type == "SCREENSHOT":
                if response.get("status") == "success":
                    img_data = base64.b64decode(response.get("data"))
                    filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    with open(filename, 'wb') as f:
                        f.write(img_data)
                    print(f"\n✓ Screenshot saved: {filename}\n")
                else:
                    print(f"\n❌ {response.get('message')}\n")
            
            elif resp_type == "DOWNLOAD":
                if response.get("status") == "success":
                    file_data = base64.b64decode(response.get("data"))
                    filename = response.get("filename")
                    with open(filename, 'wb') as f:
                        f.write(file_data)
                    print(f"\n✓ Downloaded: {filename} ({len(file_data)} bytes)\n")
                else:
                    print(f"\n❌ {response.get('message')}\n")
            
            elif resp_type == "UPLOAD":
                print(f"\n✓ {response.get('message')}\n")
            
            elif resp_type == "SYSINFO":
                print(f"\n{json.dumps(response, indent=2)}\n")
            
            else:
                print("\n" + "-"*80)
                print(json.dumps(response, indent=2))
                print("-"*80 + "\n")
        
        except:
            # Regular output
            print("\n" + "-"*80)
            print(output)
            print("-"*80 + "\n")
    
    except KeyboardInterrupt:
        print("\n\n✓ Server shutting down...")
        break
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")

print("Server stopped.")
